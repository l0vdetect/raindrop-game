#!/usr/bin/env python3
"""
RAINSTREAM COMPETITIVE - Pattern Detection & AI Competitive System
Full competitive backend with 3-difficulty AI, pattern analysis, and scoring.
"""

import argparse
import json
import sys
import cv2
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional
from enum import Enum
from datetime import datetime

class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

@dataclass
class Detection:
    x: float
    y: float
    radius: float
    frame: int
    timestamp: float
    confidence: float
    color: str = "blue"

@dataclass
class PlayerStats:
    name: str
    hits: int = 0
    misses: int = 0
    combo: int = 0
    combo_max: int = 0
    score: int = 0
    accuracy: float = 0.0
    reaction_times: List[float] = None
    pattern_bonus: int = 0
    
    def __post_init__(self):
        if self.reaction_times is None:
            self.reaction_times = []

@dataclass
class AIProfile:
    difficulty: Difficulty
    strategy: str = "CLUSTER"
    accuracy: float = 0.85
    reaction_ms: float = 150.0
    prediction_range: float = 50.0
    
    @classmethod
    def create(cls, difficulty: str):
        diff = Difficulty(difficulty)
        if diff == Difficulty.EASY:
            return cls(diff, "RANDOM", 0.45, 350.0, 30.0)
        elif diff == Difficulty.MEDIUM:
            return cls(diff, "CLUSTER", 0.75, 180.0, 60.0)
        else:  # HARD
            return cls(diff, "PREDICTIVE", 0.95, 80.0, 120.0)

class PatternDetector:
    """Detects blue circular patterns (raindrops) in video frames"""
    
    def __init__(self):
        self.lower_blue = np.array([90, 100, 100])
        self.upper_blue = np.array([130, 255, 255])
        self.detections: List[Detection] = []
    
    def detect_frame(self, frame: np.ndarray, frame_idx: int, fps: float) -> List[Detection]:
        """Detect blue circular patterns in a frame"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_blue, self.upper_blue)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        frame_detections = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if 50 < area < 5000:
                (x, y), radius = cv2.minEnclosingCircle(contour)
                if 3 < radius < 80:
                    detection = Detection(
                        x=float(x),
                        y=float(y),
                        radius=float(radius),
                        frame=frame_idx,
                        timestamp=frame_idx / fps,
                        confidence=float(area / (np.pi * radius**2)),
                        color="blue"
                    )
                    frame_detections.append(detection)
                    self.detections.append(detection)
        
        return frame_detections
    
    def process_video(self, video_path: str, duration: int = 30) -> List[Detection]:
        """Process entire video and extract detections"""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        max_frames = int(duration * fps)
        
        frame_idx = 0
        while frame_idx < min(total_frames, max_frames):
            ret, frame = cap.read()
            if not ret:
                break
            
            self.detect_frame(frame, frame_idx, fps)
            frame_idx += 1
        
        cap.release()
        return self.detections

class PatternAnalyzer:
    """Analyzes spatial and temporal patterns"""
    
    @staticmethod
    def analyze_clusters(detections: List[Detection]) -> Dict:
        """Identify spatial clustering patterns"""
        if not detections:
            return {"clusters": 0, "spread": 0}
        
        coords = np.array([[d.x, d.y] for d in detections])
        distances = np.linalg.norm(coords[:, None] - coords[None, :], axis=2)
        avg_distance = np.mean(distances[np.triu_indices_from(distances, k=1)])
        
        return {
            "clusters": int(max(1, 10 - avg_distance / 100)),
            "spread": float(avg_distance),
            "centroid": [float(np.mean(coords[:, 0])), float(np.mean(coords[:, 1]))]
        }
    
    @staticmethod
    def analyze_rhythm(detections: List[Detection]) -> Dict:
        """Analyze temporal rhythm of detections"""
        if len(detections) < 2:
            return {"rhythm_score": 0, "intervals": []}
        
        times = np.array([d.timestamp for d in detections])
        intervals = np.diff(times)
        mean_interval = float(np.mean(intervals)) if len(intervals) > 0 else 0
        std_interval = float(np.std(intervals)) if len(intervals) > 0 else 0
        
        rhythm_score = max(0, 100 - (std_interval * 100))
        
        return {
            "rhythm_score": float(rhythm_score),
            "mean_interval": mean_interval,
            "std_interval": std_interval,
            "intervals": intervals.tolist()[:20]
        }
    
    @staticmethod
    def analyze_complexity(detections: List[Detection], duration: int) -> float:
        """Calculate overall pattern complexity (0-100)"""
        if not detections:
            return 0.0
        
        density = len(detections) / max(duration, 1)
        spread = max(d.radius for d in detections) - min(d.radius for d in detections)
        
        complexity = min(100, (density * 20) + (spread * 0.5))
        return float(complexity)

class AIAgent:
    """Competitive AI opponent with 3 difficulty levels"""
    
    def __init__(self, profile: AIProfile):
        self.profile = profile
        self.stats = PlayerStats(name="AI Agent")
        self.predictions = []
    
    def process_detections(self, detections: List[Detection], time_window: float = 0.5):
        """Make AI decisions on which patterns to target"""
        recent = [d for d in detections if d.timestamp <= time_window]
        
        if not recent:
            return None
        
        if self.profile.difficulty == Difficulty.EASY:
            target = recent[np.random.randint(0, len(recent))]
        elif self.profile.difficulty == Difficulty.MEDIUM:
            target = max(recent, key=lambda d: d.radius)
        else:  # HARD
            target = recent[0]
        
        if np.random.random() < self.profile.accuracy:
            self.stats.hits += 1
            self.stats.combo += 1
            self.stats.score += 10 + self.stats.combo * 5
        else:
            self.stats.misses += 1
            self.stats.combo = 0
        
        self.stats.combo_max = max(self.stats.combo_max, self.stats.combo)
        self.predictions.append({
            "target": asdict(target),
            "hit": self.stats.hits > 0
        })
    
    def finalize_stats(self):
        """Calculate final accuracy"""
        total = self.stats.hits + self.stats.misses
        if total > 0:
            self.stats.accuracy = round(100 * self.stats.hits / total, 2)

class CompetitiveGame:
    """Main competitive game system orchestrator"""
    
    def __init__(self, video_path: str, duration: int, difficulty: str):
        self.video_path = video_path
        self.duration = duration
        self.ai_profile = AIProfile.create(difficulty)
        
        self.detector = PatternDetector()
        self.analyzer = PatternAnalyzer()
        self.ai = AIAgent(self.ai_profile)
        
        self.player1 = PlayerStats(name="Player 1")
        self.player2 = PlayerStats(name="Player 2")
        self.timestamp = datetime.now().isoformat()
    
    def run(self) -> Dict:
        """Execute full competitive analysis"""
        print(f"[RAINSTREAM] Processing: {self.video_path}")
        print(f"[RAINSTREAM] Duration: {self.duration}s | Difficulty: {self.ai_profile.difficulty.value.upper()}")
        
        detections = self.detector.process_video(self.video_path, self.duration)
        print(f"[RAINSTREAM] Detected {len(detections)} patterns")
        
        if not detections:
            print("[WARNING] No patterns detected - check video or settings")
            return self._empty_result()
        
        # Partition detections between players (left/right screen split)
        mid_x = 512  # Canvas width / 2
        p1_detections = [d for d in detections if d.x < mid_x]
        p2_detections = [d for d in detections if d.x >= mid_x]
        
        # Player 1 - left side (captures own detections with some miss rate)
        for d in p1_detections:
            if np.random.random() < 0.85:
                self.player1.hits += 1
                self.player1.combo += 1
                self.player1.score += 10 + self.player1.combo * 5
            else:
                self.player1.misses += 1
                self.player1.combo = 0
        
        # Player 2 - right side
        for d in p2_detections:
            if np.random.random() < 0.80:
                self.player2.hits += 1
                self.player2.combo += 1
                self.player2.score += 10 + self.player2.combo * 5
            else:
                self.player2.misses += 1
                self.player2.combo = 0
        
        # AI processes all detections
        self.ai.process_detections(detections, self.duration)
        
        # Finalize stats
        self.player1.combo_max = max(self.player1.combo_max, self.player1.combo)
        self.player2.combo_max = max(self.player2.combo_max, self.player2.combo)
        
        total_p1 = self.player1.hits + self.player1.misses
        total_p2 = self.player2.hits + self.player2.misses
        
        if total_p1 > 0:
            self.player1.accuracy = round(100 * self.player1.hits / total_p1, 2)
        if total_p2 > 0:
            self.player2.accuracy = round(100 * self.player2.hits / total_p2, 2)
        
        self.ai.finalize_stats()
        
        # Pattern analysis
        cluster_analysis = self.analyzer.analyze_clusters(detections)
        rhythm_analysis = self.analyzer.analyze_rhythm(detections)
        complexity = self.analyzer.analyze_complexity(detections, self.duration)
        
        # Ranking
        ranking = sorted([
            {"rank": 1, "name": "P1", "score": self.player1.score, "type": "player"},
            {"rank": 2, "name": "AI", "score": self.ai.stats.score, "type": "ai"},
            {"rank": 3, "name": "P2", "score": self.player2.score, "type": "player"}
        ], key=lambda x: x["score"], reverse=True)
        
        for i, item in enumerate(ranking, 1):
            item["rank"] = i
        
        return {
            "metadata": {
                "timestamp": self.timestamp,
                "video": Path(self.video_path).name,
                "duration_seconds": self.duration,
                "total_patterns": len(detections)
            },
            "player1": asdict(self.player1),
            "player2": asdict(self.player2),
            "ai": {
                **asdict(self.ai.stats),
                "difficulty": self.ai_profile.difficulty.value,
                "strategy": self.ai_profile.strategy
            },
            "analysis": {
                "pattern_complexity": complexity,
                "cluster_analysis": cluster_analysis,
                "rhythm_analysis": rhythm_analysis,
                "total_detections": len(detections),
                "p1_detections": len(p1_detections),
                "p2_detections": len(p2_detections)
            },
            "ranking": ranking,
            "game_status": "COMPLETED"
        }
    
    def _empty_result(self) -> Dict:
        """Return empty result when no detections found"""
        return {
            "metadata": {
                "timestamp": self.timestamp,
                "video": Path(self.video_path).name,
                "duration_seconds": self.duration,
                "total_patterns": 0
            },
            "player1": asdict(self.player1),
            "player2": asdict(self.player2),
            "ai": asdict(self.ai.stats),
            "analysis": {
                "pattern_complexity": 0,
                "cluster_analysis": {"clusters": 0, "spread": 0},
                "rhythm_analysis": {"rhythm_score": 0, "intervals": []}
            },
            "ranking": [
                {"rank": 1, "name": "P1", "score": 0},
                {"rank": 2, "name": "AI", "score": 0},
                {"rank": 3, "name": "P2", "score": 0}
            ],
            "game_status": "NO_PATTERNS_DETECTED"
        }

def main():
    parser = argparse.ArgumentParser(description="RAINSTREAM COMPETITIVE - Pattern Detection Game")
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("--duration", type=int, default=30, help="Game duration in seconds")
    parser.add_argument("--ai-difficulty", choices=["easy", "medium", "hard"], default="medium", help="AI difficulty level")
    parser.add_argument("--output", help="Output JSON file path")
    
    args = parser.parse_args()
    
    if not Path(args.video).exists():
        print(f"[ERROR] Video not found: {args.video}")
        sys.exit(1)
    
    game = CompetitiveGame(args.video, args.duration, args.ai_difficulty)
    results = game.run()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"[RAINSTREAM] Results saved to: {args.output}")
    else:
        print(json.dumps(results, indent=2))
    
    print(f"[RAINSTREAM] GAME OVER")
    print(f"  P1: {results['player1']['score']} pts | AI: {results['ai']['score']} pts | P2: {results['player2']['score']} pts")

if __name__ == "__main__":
    main()
