# video_player.py
import pygame
import cv2 
import numpy


class VideoPlayer:
    def __init__(self, video_path, target_size, forced_fps=None):
        self.video_path = video_path
        self.target_size = target_size
        self.cap = None
        self.is_playing = False
        self.total_frames = 0
        self.fps = 0
        self.current_frame_surface = None
        
        self.frame_count_for_current_playthrough = 0
        
        self.current_decoded_frame_number = -1

        try:
            self.cap = cv2.VideoCapture(self.video_path)
            if not self.cap.isOpened():
                print(f"Error: Could not open video file: {self.video_path}")
                self.cap = None
                return

            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

            if forced_fps is not None and forced_fps > 0:
                self.fps = forced_fps
                print(f"Video loaded: {self.video_path}, FPS: {self.fps} (FORCED), Frames: {self.total_frames}")
            else:
                reported_fps = self.cap.get(cv2.CAP_PROP_FPS)
                if reported_fps > 0:
                    self.fps = reported_fps
                    print(
                        f"Video loaded: {self.video_path}, FPS: {self.fps} (Reported by OpenCV), Frames: {self.total_frames}")
                else:  
                    self.fps = 30.0
                    print(
                        f"Video loaded: {self.video_path}, FPS: {self.fps} (FALLBACK, OpenCV reported {reported_fps}), Frames: {self.total_frames}")

            if self.total_frames > 0 and self.fps > 0:
                self.is_playing = True
             
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame_bgr = self.cap.read()
                if ret:
                    self.current_decoded_frame_number = 0
                    self.current_frame_surface = self._process_bgr_frame(frame_bgr)
                    self.frame_count_for_current_playthrough = 1
                else:
                    print(f"Warning: Could not read initial frame from {self.video_path}")
                    self.is_playing = False
            else:
                print(
                    f"Warning: Video has no frames or invalid FPS. Total frames: {self.total_frames}, FPS: {self.fps}")
                self.is_playing = False


        except Exception as e:
            print(f"Exception during VideoPlayer init for {self.video_path}: {e}")
            if self.cap: self.cap.release()
            self.cap = None
            self.is_playing = False

    def _process_bgr_frame(self, frame_bgr):
        if frame_bgr is None:
            return None
        try:
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, self.target_size, interpolation=cv2.INTER_LINEAR)
            pygame_surface = pygame.image.frombuffer(frame_resized.tobytes(), frame_resized.shape[1::-1], "RGB")
            return pygame_surface
        except cv2.error as e:
            print(f"OpenCV error during frame processing: {e}")
            return None

    def get_frame_at_time(self, time_ms):
        if not self.is_valid():
            return self.current_frame_surface

        target_frame_index = int((time_ms / 1000.0) * self.fps)

        if target_frame_index < 0: target_frame_index = 0
        
        if target_frame_index >= self.total_frames and self.total_frames > 0:
            target_frame_index = self.total_frames - 1

        
        self.frame_count_for_current_playthrough = target_frame_index + 1

        frame_bgr = None
        ret = False

        try:
            if target_frame_index == self.current_decoded_frame_number:
                
                return self.current_frame_surface

            
            elif target_frame_index == self.current_decoded_frame_number + 1:
            
                ret, frame_bgr = self.cap.read()
            
            else:
            
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_index)
                ret, frame_bgr = self.cap.read()

            if ret and frame_bgr is not None:
                self.current_frame_surface = self._process_bgr_frame(frame_bgr)
                self.current_decoded_frame_number = target_frame_index
            
                pass


        except cv2.error as e:
            print(f"OpenCV error during frame fetch for time {time_ms}ms, target_frame {target_frame_index}: {e}")
            

        return self.current_frame_surface

    def get_current_surface(self):
        return self.current_frame_surface

    def release(self):
        if self.cap:
            self.cap.release()
        self.is_playing = False
        self.cap = None
        print(f"VideoPlayer {self.video_path} released.")

    def is_valid(self):
        
        return self.cap is not None and self.cap.isOpened() and self.is_playing and self.total_frames > 0 and self.fps > 0

    def is_one_playthrough_done(self):
        if self.total_frames <= 0: return True  
        
        return self.frame_count_for_current_playthrough >= self.total_frames

    def reset_playthrough_counter(self):
        self.frame_count_for_current_playthrough = 0
        self.current_decoded_frame_number = -1  
        if self.cap and self.cap.isOpened():  
            try:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame_bgr = self.cap.read()
                if ret:
                    self.current_decoded_frame_number = 0
                    self.current_frame_surface = self._process_bgr_frame(frame_bgr)
                    self.frame_count_for_current_playthrough = 1
                else:
                    print(
                        f"Warning: Could not read initial frame during reset_playthrough_counter for {self.video_path}")
                   
            except cv2.error as e:
                print(f"OpenCV error during reset_playthrough_counter: {e}")
        elif not (self.cap and self.cap.isOpened()) and self.video_path:
            print(f"VideoPlayer: Cap was not opened in reset. Attempting to reopen {self.video_path}")
            self.cap = cv2.VideoCapture(self.video_path)
            if self.cap.isOpened():
                print(f"VideoPlayer: Successfully reopened {self.video_path}")
                self.is_playing = True
                self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
              
                self.reset_playthrough_counter() 
            else:
                print(f"VideoPlayer: Failed to reopen {self.video_path} in reset.")
                self.is_playing = False
                self.cap = None 