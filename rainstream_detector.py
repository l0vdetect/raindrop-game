#!/usr/bin/env python3
"""
RAINSTREAM - Real-time Raindrop Pattern Recognition & Detection
Detects bright raindrop regions in windshield video, enables interactive clicking,
tracks hits/misses, and produces comprehensive JSON session data.
"""

import cv2
import json
import numpy as np
import argparse
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import math

class RaindropDetector:
    """Detects bright raindrop regions using adaptive thresholding and contour analysis."""
    
    def __init__(self, blur_kernel=15, threshold_value=200, min_area=20, max_area=5000):
        self.blur_kernel = blur_kernel
        self.threshold_value = threshold_value
        self.min_area = min_area
        self.max_area = max_area
    
    def detect_droplets(self, frame):
        """Detect bright raindrops in a frame."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (self.blur_kernel, self.blur_kernel), 0)
        _, thresh = cv2.threshold(blurred, self.threshold_value, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        droplets = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_area or area > self.max_area:
                continue
            (cx, cy), radius = cv2.minEnclosingCircle(contour)
            if radius < 2:
                continue
            droplets.append({'x': int(cx), 'y': int(cy), 'radius': int(radius), 'area': int(area)})
        return droplets
    
    def is_click_hit(self, click_x, click_y, droplets, click_tolerance=15):
        """Check if a click intersects with any droplet."""
        nearest_distance = float('inf')
        hit_droplet = None
        
        for droplet in droplets:
            dx = droplet['x'] - click_x
            dy = droplet['y'] - click_y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < droplet['radius'] + click_tolerance:
                return (True, distance, droplet)
            if distance < nearest_distance:
                nearest_distance = distance
        
        return (False, nearest_distance, None)


class RainstreamSession:
    """Manages a complete raindrop detection game session."""
    
    def __init__(self, video_path, duration_sec=30):
        self.video_path = str(video_path)
        self.duration_sec = duration_sec
        self.start_time = datetime.now()
        self.session_id = self.start_time.strftime("%Y%m%d_%H%M%S")
        
        self.cap = cv2.VideoCapture(self.video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.target_frames = int(self.fps * self.duration_sec)
        
        self.detector = RaindropDetector()
        self.frames_processed = 0
        self.current_frame_index = 0
        self.current_timestamp = 0.0
        self.detections_per_frame = {}
        self.click_events = []
        self.total_clicks = 0
        self.hits = 0
        self.misses = 0
        self.total_droplets_detected = 0
        self.current_droplets = []
        self.current_frame = None
        self.display_frame = None
    
    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.handle_click(x, y)
    
    def handle_click(self, x, y):
        """Process a mouse click."""
        is_hit, distance, hit_droplet = self.detector.is_click_hit(x, y, self.current_droplets)
        
        self.total_clicks += 1
        if is_hit:
            self.hits += 1
        else:
            self.misses += 1
        
        event_data = {
            'click_number': self.total_clicks,
            'timestamp_sec': round(self.current_timestamp, 3),
            'frame_index': self.current_frame_index,
            'click_x': x,
            'click_y': y,
            'hit': is_hit,
            'nearest_droplet_distance': round(distance, 1),
            'droplets_on_frame': len(self.current_droplets)
        }
        
        if hit_droplet:
            event_data['hit_droplet'] = {'x': hit_droplet['x'], 'y': hit_droplet['y'], 'radius': hit_droplet['radius']}
        
        self.click_events.append(event_data)
        
        color = (0, 255, 0) if is_hit else (0, 0, 255)
        cv2.circle(self.display_frame, (x, y), 20, color, 2)
        cv2.putText(self.display_frame, 'HIT' if is_hit else 'MISS', (x + 25, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    def process_frame(self, frame):
        """Process a single frame: detect droplets, draw overlays."""
        droplets = self.detector.detect_droplets(frame)
        self.current_droplets = droplets
        self.current_frame = frame.copy()
        self.display_frame = frame.copy()
        
        self.detections_per_frame[self.current_frame_index] = {
            'timestamp_sec': round(self.current_timestamp, 3),
            'droplet_count': len(droplets),
            'droplets': [{'x': d['x'], 'y': d['y'], 'radius': d['radius'], 'area': d['area']} for d in droplets]
        }
        
        self.total_droplets_detected += len(droplets)
        
        for droplet in droplets:
            cv2.circle(self.display_frame, (droplet['x'], droplet['y']), droplet['radius'], (0, 255, 255), 2)
            cv2.circle(self.display_frame, (droplet['x'], droplet['y']), 3, (0, 255, 255), -1)
        
        self.draw_hud()
        return self.display_frame
    
    def draw_hud(self):
        """Draw heads-up display with stats."""
        h, w = self.display_frame.shape[:2]
        overlay = self.display_frame.copy()
        cv2.rectangle(overlay, (10, 10), (350, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.3, self.display_frame, 0.7, 0, self.display_frame)
        
        text_color = (0, 255, 255)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        
        texts = [
            f"Time: {self.current_timestamp:.1f}s / {self.duration_sec}s",
            f"Droplets: {len(self.current_droplets)}",
            f"Clicks: {self.total_clicks} | Hits: {self.hits} | Misses: {self.misses}",
            f"Accuracy: {self.get_accuracy():.1f}%"
        ]
        
        y_pos = 35
        for text in texts:
            cv2.putText(self.display_frame, text, (20, y_pos), font, font_scale, text_color, thickness)
            y_pos += 25
        
        cv2.putText(self.display_frame, "Click raindrops | ESC to quit", (w - 400, h - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def get_accuracy(self):
        if self.total_clicks == 0:
            return 0.0
        return (self.hits / self.total_clicks) * 100
    
    def run(self):
        """Main session loop."""
        print(f"\n{'='*70}")
        print(f"RAINSTREAM - Real-time Raindrop Detection")
        print(f"{'='*70}")
        print(f"Video: {self.video_path}")
        print(f"Duration: {self.duration_sec} seconds")
        print(f"FPS: {self.fps}")
        print(f"Resolution: {self.frame_width}x{self.frame_height}")
        print(f"Target frames: {self.target_frames}")
        print(f"\nControls: Click raindrops | ESC to quit")
        print(f"{'='*70}\n")
        
        window_name = 'RAINSTREAM - Click Raindrops'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(window_name, self.mouse_callback)
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("End of video reached.")
                break
            
            if self.frames_processed >= self.target_frames:
                print(f"Duration limit reached ({self.duration_sec}s).")
                break
            
            self.current_timestamp = self.frames_processed / self.fps
            display_frame = self.process_frame(frame)
            cv2.imshow(window_name, display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                print("User quit.")
                break
            
            self.frames_processed += 1
            self.current_frame_index += 1
            
            if self.frames_processed % int(self.fps) == 0:
                print(f"  {self.current_timestamp:.1f}s - {len(self.current_droplets)} droplets detected")
        
        self.cap.release()
        cv2.destroyAllWindows()
        print(f"\n{'='*70}\nSession Complete\n{'='*70}\n")
    
    def to_dict(self):
        return {
            'session_id': self.session_id,
            'timestamp': self.start_time.isoformat(),
            'video_file': Path(self.video_path).name,
            'video_path': self.video_path,
            'duration_sec': self.duration_sec,
            'fps': self.fps,
            'resolution': {'width': self.frame_width, 'height': self.frame_height},
            'frames': {'processed': self.frames_processed, 'target': self.target_frames},
            'detections': {
                'total_droplets': self.total_droplets_detected,
                'avg_droplets_per_frame': round(self.total_droplets_detected / max(1, self.frames_processed), 2),
                'per_frame': self.detections_per_frame
            },
            'interaction': {
                'total_clicks': self.total_clicks,
                'hits': self.hits,
                'misses': self.misses,
                'accuracy_percent': round(self.get_accuracy(), 2),
                'click_events': self.click_events
            },
            'summary': {'status': 'completed', 'notes': f"Processed {self.frames_processed} frames over {self.current_timestamp:.1f} seconds"}
        }
    
    def save_json(self, output_path=None):
        if output_path is None:
            output_path = f"rainstream_session_{self.session_id}.json"
        data = self.to_dict()
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        return output_path
    
    def print_summary(self):
        print(f"\n{'='*70}\nSESSION SUMMARY\n{'='*70}")
        print(f"Duration: {self.current_timestamp:.1f}s")
        print(f"Frames processed: {self.frames_processed}")
        print(f"Total droplets detected: {self.total_droplets_detected}")
        print(f"Avg droplets per frame: {self.total_droplets_detected / max(1, self.frames_processed):.1f}\n")
        print(f"Total clicks: {self.total_clicks}")
        print(f"Hits: {self.hits}")
        print(f"Misses: {self.misses}")
        print(f"Accuracy: {self.get_accuracy():.1f}%")
        print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description='RAINSTREAM - Real-time Raindrop Pattern Recognition')
    parser.add_argument('video', help='Path to MP4 video file')
    parser.add_argument('--duration', type=int, default=30, help='Session duration in seconds (default: 30)')
    parser.add_argument('--output', default=None, help='Output JSON path')
    
    args = parser.parse_args()
    
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"Error: Video file not found: {args.video}")
        sys.exit(1)
    
    session = RainstreamSession(args.video, args.duration)
    session.run()
    session.print_summary()
    
    output_path = session.save_json(args.output)
    print(f"Session data saved: {output_path}\n")
    
    data = session.to_dict()
    print("JSON Output Preview:")
    print("-" * 70)
    print(json.dumps({
        'session_id': data['session_id'],
        'video_file': data['video_file'],
        'duration_sec': data['duration_sec'],
        'frames_processed': data['frames']['processed'],
        'detections': data['detections'],
        'interaction': data['interaction']
    }, indent=2))
    print("-" * 70)


if __name__ == '__main__':
    main()
