import re
import time
import collections
import numpy as np
import sounddevice as sd
import webrtcvad
from PyQt6.QtCore import QThread, pyqtSignal

_RATE           = 16000
_CHANNELS       = 1
_FRAME_MS       = 30                              # VAD requires 10/20/30 ms frames
_FRAME_SAMPLES  = int(_RATE * _FRAME_MS / 1000)  # 480 samples per frame
_SILENCE_MS     = 800                             # stop after 0.8 s of silence post-speech
_SILENCE_FRAMES = _SILENCE_MS // _FRAME_MS        # 26 frames
_MIN_SPEECH_FRAMES = 300 // _FRAME_MS             # ignore bursts shorter than 300 ms
_MAX_RECORD_S   = 10
_PREROLL_FRAMES = 10                              # keep 300 ms of pre-speech audio


def parse_voice_command(text):
    """
    Parse a voice transcript into grade / comment / action.
    Recognises (case-insensitive, any order):
        Grade <X>   — everything after 'grade' until next keyword or end
        Comment <…> — everything after 'comment' until 'next'/'previous'/end
        Next / Previous — navigation action
    Examples
        "Grade A Comment nice galaxy Next"  → grade='a', comment='nice galaxy', action='next'
        "Grade A Next"                      → grade='a', action='next'
        "Comment merger candidate Previous" → comment='merger candidate', action='previous'
        "Next"                              → action='next'
    """
    t = text.lower().strip()
    # Replace punctuation that speech-to-text adds around keywords
    # (e.g. "Comment, nice object" / "Grade, A" / "Next." / "Comment: text")
    # Use space so adjacent words don't merge ("great.Next" → "great next")
    t = re.sub(r'[,.:;!?]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()

    action = None
    if re.search(r'\bnext\b', t):
        action = 'next'
    elif re.search(r'\bprevious\b', t):
        action = 'previous'

    grade = None
    m = re.search(r'\bgrade\b\s+(.*?)(?=\bcomment\b|\bnext\b|\bprevious\b|$)', t, re.DOTALL)
    if m:
        g = m.group(1).strip().replace(',', '').replace('.', '')
        grade = g or None

    comment = None
    m = re.search(r'\bcomment\b\s+(.*?)(?=\bnext\b|\bprevious\b|$)', t, re.DOTALL)
    if m:
        c = m.group(1).strip()
        comment = c or None

    return {'grade': grade, 'comment': comment, 'action': action}


class VoiceOverThread(QThread):
    command_parsed   = pyqtSignal(dict)   # {'grade': str|None, 'comment': str|None, 'action': str|None}
    listening        = pyqtSignal()       # mic is open, waiting for speech
    processing       = pyqtSignal()       # transcription in progress
    transcript_ready = pyqtSignal(str)    # raw recognised text
    status_update    = pyqtSignal(str)    # one-off info message (e.g. model loading)
    error            = pyqtSignal(str)    # error message

    def __init__(self, model_size='base', parent=None):
        super().__init__(parent)
        self.model_size = model_size
        self._active = False
        self._model = None

    def start_listening(self):
        self._active = True
        if not self.isRunning():
            self.start()

    def stop_listening(self):
        self._active = False

    def _load_model(self):
        from faster_whisper import WhisperModel
        self.status_update.emit('Loading model...')
        self._model = WhisperModel(self.model_size, device='cpu', compute_type='auto')

    def _transcribe(self, frames):
        # Raw int16 PCM → float32 numpy array; passed directly to faster-whisper
        # so av / metadata_errors is never involved.
        audio = np.frombuffer(b''.join(frames), dtype=np.int16).astype(np.float32) / 32768.0
        segments, _ = self._model.transcribe(
            audio,
            language='en',
            condition_on_previous_text=False,
            beam_size=1,
        )
        return ' '.join(s.text.strip() for s in segments).strip()

    def run(self):
        if self._model is None:
            try:
                self._load_model()
            except Exception as e:
                msg = f'Model load failed: {e}'
                print(f'[VoiceOver] {msg}')
                self.error.emit(msg)
                return

        vad = webrtcvad.Vad(3)   # mode 3: most aggressive

        while self._active:
            # ── Open mic ────────────────────────────────────────────
            try:
                stream = sd.RawInputStream(
                    samplerate=_RATE, channels=_CHANNELS,
                    dtype='int16', blocksize=_FRAME_SAMPLES,
                )
                stream.start()
            except Exception as e:
                msg = f'Mic error: {e}'
                print(f'[VoiceOver] {msg}')
                self.error.emit(msg)
                break

            self.listening.emit()

            # ── VAD recording loop ──────────────────────────────────
            preroll  = collections.deque(maxlen=_PREROLL_FRAMES)
            speech   = []
            silent   = 0
            speaking = False
            max_frames = int(_RATE / _FRAME_SAMPLES * _MAX_RECORD_S)

            try:
                while self._active and (len(speech) + len(preroll)) < max_frames:
                    raw, _ = stream.read(_FRAME_SAMPLES)
                    data = bytes(raw)
                    is_speech = vad.is_speech(data, _RATE)

                    if not speaking:
                        preroll.append(data)
                        if is_speech:
                            speaking = True
                            speech.extend(preroll)
                            preroll.clear()
                    else:
                        speech.append(data)
                        if is_speech:
                            silent = 0
                        else:
                            silent += 1
                            if silent >= _SILENCE_FRAMES:
                                break
            finally:
                stream.stop()
                stream.close()

            if not self._active:
                break

            # Skip if too short (noise burst, not real speech)
            if len(speech) < _MIN_SPEECH_FRAMES:
                continue

            # ── Transcribe ──────────────────────────────────────────
            self.processing.emit()
            try:
                text = self._transcribe(speech)
            except Exception as e:
                msg = f'Transcription error: {e}'
                print(f'[VoiceOver] {msg}')
                self.error.emit(msg)
                time.sleep(2)
                continue

            if not text:
                continue

            print(f'[VoiceOver] "{text}"')
            self.transcript_ready.emit(text)
            parsed = parse_voice_command(text)
            if any(v is not None for v in parsed.values()):
                self.command_parsed.emit(parsed)
