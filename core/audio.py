import sounddevice as sd
import queue
import sys
import numpy as np
import collections

try:
    import webrtcvad
    HAS_VAD = True
except ImportError:
    HAS_VAD = False
    print("Warning: webrtcvad module not found. VAD disabled (Energy detection fallback used).")

class AudioCapture:
    def __init__(self, device_index=None, sample_rate=16000, frame_duration_ms=30, energy_threshold=300):
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        self.device_index = device_index
        
        self.vad = None
        if HAS_VAD:
            # Level 2 is a good balance for all environments
            self.vad = webrtcvad.Vad(2) 
            
        self.audio_queue = queue.Queue()
        self.running = False
        self.stream = None
        self.is_listening = False

        # Energy based VAD fallback
        self.energy_threshold = energy_threshold
        self.noise_floor = 0
        self.silence_frames = 0
        self.calibration_frames = 20
        self.calibrating = False
        self.manual_threshold = True

        # Advanced Filtering
        # 1. Pre-roll buffer: Keep last 210ms (7 frames of 30ms) to avoid cutting word starts
        self.pre_roll_frames = 7
        self.pre_roll_buffer = collections.deque(maxlen=self.pre_roll_frames)
        
        # 2. Duration filter: Must have X continuous frames of speech to trigger
        # Level 2 VAD + Energy is good. We require ~150ms (5 frames) of speech 
        # to ignore snaps/claps (which are usually 1-2 frames)
        self.speech_frames_count = 0
        self.min_speech_frames = 5 
        
        # 3. Post-roll (Grace period): How much silence before stopping
        # 15 frames = 450ms. Good for natural pauses.
        self.post_speech_silence_threshold = 15

    def start(self):
        self.running = True
        try:
            self.stream = sd.InputStream(
                device=self.device_index,
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16',
                blocksize=self.frame_size,
                callback=self._audio_callback
            )
            self.stream.start()
            self.calibrating = True
            print(f"Audio stream started on device {self.device_index if self.device_index else 'Default'}.")
        except Exception as e:
            print(f"Failed to start audio stream: {e}")
            self.running = False

    def stop(self):
        self.running = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

    def change_device(self, new_device_index):
        self.stop()
        self.device_index = new_device_index
        self.start()

    def update_threshold(self, new_threshold):
        self.energy_threshold = new_threshold

    def get_devices(self):
        devices = []
        try:
            full_list = sd.query_devices()
            default_index = sd.query_devices(kind='input')['index']
            for i, dev in enumerate(full_list):
                if dev['max_input_channels'] > 0 and dev.get('default_samplerate', 0) > 0:
                    name = dev['name']
                    if i == default_index: name = f"⭐ {name} (Padrão)"
                    devices.append({'index': i, 'name': name})
        except: pass
        return devices

    def _audio_callback(self, indata, frames, time, status):
        audio_bytes = indata.tobytes()
        if len(audio_bytes) == 0: return

        # 1. Store in pre-roll buffer
        self.pre_roll_buffer.append(audio_bytes)

        # 2. Basic detection (Energy + WebRTC)
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
        energy = np.sqrt(np.mean(audio_np.astype(np.float32)**2)) if len(audio_np) > 0 else 0
        
        raw_speech = energy > self.energy_threshold
        if self.vad:
            try:
                raw_speech = self.vad.is_speech(audio_bytes, self.sample_rate) and raw_speech
            except: raw_speech = True

        # 3. Duration Filtering (Ignore short noises like snaps)
        if raw_speech:
            self.speech_frames_count += 1
            if self.speech_frames_count >= self.min_speech_frames:
                if not self.is_listening:
                    print(f"VAD: Fala detectada (Energia: {energy:.0f})")
                    # When starting, push the pre-roll buffer so we don't lose the start of the word
                    if self.running:
                        for frame in list(self.pre_roll_buffer)[:-1]: # All but current
                            self.audio_queue.put((frame, True, energy))
                self.is_listening = True
                self.silence_frames = 0
        else:
            self.speech_frames_count = 0
            self.silence_frames += 1
            if self.silence_frames > self.post_speech_silence_threshold:
                if self.is_listening:
                    print(f"VAD: Fim de fala detectado.")
                self.is_listening = False

        # 4. Push current frame if listening
        if self.running:
            self.audio_queue.put((audio_bytes, bool(self.is_listening), int(energy)))

    def get_audio(self):
        try:
            return self.audio_queue.get(timeout=0.1)
        except queue.Empty:
            return None, False
