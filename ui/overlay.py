from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtGui import QFont, QColor, QPalette, QPainter, QBrush, QPen, QIcon
from ui.settings import SettingsDialog
import json

class OverlayWindow(QWidget):
    request_restart_audio = Signal(int) # Signal to main thread to restart audio
    request_full_restart = Signal() # New signal for model/lang changes
    closed_signal = Signal() # New signal to tell main to quit

    def __init__(self, config=None, audio_handler=None):
        super().__init__()
        self.config = config or {}
        self.audio_handler = audio_handler
        self.setWindowTitle("OmniTranslator")
        self.version = "1.0.0"
        
        # Window Flags
        flags = Qt.FramelessWindowHint | Qt.Tool
        if self.config.get("always_on_top", True):
            flags |= Qt.WindowStaysOnTopHint
        
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Background Opacity
        self.background_opacity = self.config.get("opacity", 0.7)
        
        # Layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(20, 0, 20, 10)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)
        
        # Floating Controls Container (not in layout to not take space)
        self.settings_btn = QPushButton("⚙️", self)
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.setStyleSheet("background-color: transparent; color: white; border: none; font-size: 16px;")
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.clicked.connect(self.open_settings)
        
        self.status_label = QLabel("⏸", self)
        self.status_label.setFont(QFont("Segoe UI Emoji", 16))
        self.status_label.setStyleSheet("color: red;")
        
        self.pause_label = QLabel("⏸", self)
        self.pause_label.setFont(QFont("Segoe UI Emoji", 16))
        self.pause_label.setStyleSheet("color: orange;")
        self.pause_label.setVisible(False) # Começa oculto
        
        self.close_btn = QPushButton("❌", self)
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setStyleSheet("background-color: transparent; border: none; font-size: 12px;")
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.close)

        # Text Area Container (Dynamic Alignment)
        self.text_area_layout = QVBoxLayout()
        self.text_area_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self.text_area_layout)

        # Text Display
        self.text_label = QLabel("Waiting for speech...")
        self.text_label.setWordWrap(True)
        # Transmit mouse events to parent for dragging anywhere
        self.text_label.setAttribute(Qt.WA_TransparentForMouseEvents) 

        # Fade Animation
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        from PySide6.QtCore import QPropertyAnimation
        self.opacity_effect = QGraphicsOpacityEffect(self.text_label)
        self.text_label.setGraphicsEffect(self.opacity_effect)
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(300) # 300ms fade
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)

        from collections import deque
        self.history = deque(maxlen=2) # Initialize early
        self.max_display_chars = 300 
        
        # Apply styles (this uses self.history now)
        self.apply_font_style()
        
        # Position
        screen_geometry = QApplication.primaryScreen().geometry()
        width = 1000 
        height = 240 # High enough for 2 vertical blocks
        self.resize(width, height)

        
        x_pos = self.config.get("x_pos")
        y_pos = self.config.get("y_pos", 50)
        
        if x_pos is None:
            x_pos = screen_geometry.width() // 2 - width // 2
            
        self.move(int(x_pos), int(y_pos)) # Ensure ints
        self.old_pos = None

    def apply_font_style(self):
        # Apply window size changes
        width = self.config.get("win_width", 1000)
        height = self.config.get("win_height", 240)
        self.setFixedSize(width, height)
        
        # Posicionamento Absoluto dos Ícones (Floating)
        self.settings_btn.move(10, 5)
        self.pause_label.move(width - 105, 5)
        self.status_label.move(width - 70, 5)
        self.close_btn.move(width - 35, 5)

        # Alinhamento Dinâmico (Hotta Tecnologia)
        align_type = self.config.get("text_align", "top")
        
        # Garante que o container de texto é o único no layout principal
        if self.main_layout.indexOf(self.text_area_layout) == -1:
            self.main_layout.addLayout(self.text_area_layout)

        # Limpa o container interno de texto
        while self.text_area_layout.count():
            item = self.text_area_layout.takeAt(0)
            if item.widget() == self.text_label:
                self.text_label.setParent(None)

        # 2. Reconstrói baseado no alinhamento
        if align_type == "center":
            self.text_area_layout.addStretch()
            self.text_label.setAlignment(Qt.AlignCenter)
        elif align_type == "bottom":
            self.text_area_layout.addStretch()
            self.text_label.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        else: # top - Encostado MESMO
            self.text_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.text_area_layout.addWidget(self.text_label)

        if align_type == "top" or align_type == "center":
            self.text_area_layout.addStretch()

        # Apply Font
        font = QFont("Arial", 12, QFont.Bold)
        self.text_label.setFont(font)
        
        # Hotta: Espaçamento sutil no topo para não ficar "colado" demais
        if align_type == "top":
            self.text_label.setStyleSheet("padding: 0px; margin-top: 10px;")
        else:
            self.text_label.setStyleSheet("padding: 15px;")
        
        # Update flags
        flags = Qt.FramelessWindowHint | Qt.Tool
        if self.config.get("always_on_top", True):
            flags |= Qt.WindowStaysOnTopHint
        
        if self.windowFlags() != flags:
            self.setWindowFlags(flags)
            self.show()


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Transparent background for the widget itself
        # The actual look comes from the painting below
        
        # Draw background with rounded corners and subtle border
        rect = self.rect()
        
        # 1. Main Background
        bg_color = QColor(20, 20, 20, int(255 * self.background_opacity))
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 15, 15)
        
        # 2. Glassy Border (Top/Left highlight)
        border_pen = QPen(QColor(255, 255, 255, 50)) # Subtle white
        border_pen.setWidth(1)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect.adjusted(1,1,-1,-1), 15, 15)
        
        # 3. Drag Handle Hint (Top Center)
        handle_pen = QPen(QColor(255, 255, 255, 80))
        handle_pen.setWidth(2)
        handle_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(handle_pen)
        center_x = rect.width() // 2
        painter.drawLine(center_x - 15, 5, center_x + 15, 5) # Small line at top
        painter.drawLine(center_x - 10, 8, center_x + 10, 8) # Smaller line below

    def set_version(self, version):
        self.version = version

    def open_settings(self):
        # SNAPSHOT categorical values to check for changes
        old_dev = self.config.get("audio_device_index")
        old_model = self.config.get("model_type", "small")
        old_lang = self.config.get("target_lang", "en")
        old_vad = self.config.get("vad_threshold", 300)
        
        dialog = SettingsDialog(self, self.config, self.audio_handler, current_version=self.version)
        if dialog.exec():
            # Settings were saved to self.config in-place
            self.apply_font_style()
            self.background_opacity = self.config.get("opacity", 0.7)
            self.update() # trigger repaint
            
            # Now compare with snapshot
            new_dev = self.config.get("audio_device_index")
            new_model = self.config.get("model_type", "small")
            new_lang = self.config.get("target_lang", "en")
            new_vad = self.config.get("vad_threshold", 300)
            
            if new_vad != old_vad and self.audio_handler:
                 self.audio_handler.update_threshold(new_vad)

            if new_model != old_model or new_lang != old_lang:
                 self.request_full_restart.emit()
            elif new_dev != old_dev:
                 # ONLY restart audio if the device index actually changed
                 self.request_restart_audio.emit(new_dev)

            
            # Save to file
            try:
                with open('config.json', 'w') as f:
                    json.dump(self.config, f)
            except Exception as e:
                print(f"Error saving config: {e}")

    def closeEvent(self, event):
        self.closed_signal.emit()
        event.accept()

    @Slot(str, str)
    def update_text(self, transcription, translation, to_history=True):
        # Get styles from config with defaults
        t_color = self.config.get("trans_color", "#39FF14")
        t_size = self.config.get("trans_font_size", 24)
        o_color = self.config.get("orig_color", "white")
        o_size = self.config.get("orig_font_size", 16)
        
        # 1. Handle "Clear" or empty calls
        if not transcription and not translation:
             self.text_label.setText("")
             return

        # NEW: Logic to find and update existing entry if it's the same transcription
        # This allows Portugese to show up FIRST, then be replaced by PT+EN
        existing_idx = -1
        if translation and to_history:
            for i, item in enumerate(self.history):
                 # We look for the exact partial HTML we generated below
                 if f"<div style='color: orange; font-style: italic; font-size: 14px;'>... {transcription}</div>" in item:
                     existing_idx = i
                     break

        if translation:
            # 2. Final result with translation
            # Vertical Block Layout:
            # [ TRANSLATION (GREEN, BIG) ]
            # [ Original (Secondary, Small) ]
            
            if translation.strip().lower() == transcription.strip().lower():
                # If identical, just show one bold line
                segment = f"<div style='margin-bottom: 20px;'><div style='color: {t_color}; font-size: {t_size}px; font-weight: bold;'>{translation}</div></div>"
            else:
                segment = (
                    f"<div style='margin-bottom: 20px;'>"
                    f"  <div style='color: {t_color}; font-size: {t_size}px; font-weight: bold;'>{translation}</div>"
                    f"  <div style='color: {o_color}; font-size: {o_size}px; opacity: 0.8;'>{transcription}</div>"
                    f"</div>"
                )
            
            if to_history:
                # Update existing entry if found, otherwise append
                if existing_idx >= 0:
                    self.history[existing_idx] = segment
                else:
                    # Avoid duplicates
                    if not self.history or self.history[-1] != segment:
                        self.history.append(segment)
            
            # Roll text
            while len(self.history) > 2: # Keep only last 2 blocks for vertical stability
                self.history.popleft()
                
            full_html = "".join(self.history) 
            self.text_label.setText(f"<html><body>{full_html}</body></html>")
            self.fade_animation.start()
        elif transcription:
            # 3. Partial result or Status
            hist_str = "".join(self.history)
            
            if not to_history:
                # Temporary status like "Carregando..."
                status_html = f"<div style='color: orange; font-style: italic; font-size: 14px;'>{transcription}</div>"
                full_html = f"{hist_str}{status_html}"
            else:
                # Real partial transcription (final segment but not translated yet)
                partial_html = f"<div style='color: orange; font-style: italic; font-size: 14px;'>... {transcription}</div>"
                
                if not self.history or self.history[-1] != partial_html:
                    self.history.append(partial_html)
                
                while len(self.history) > 2:
                    self.history.popleft()
                
                full_html = "".join(self.history)
            
            self.text_label.setText(f"<html><body>{full_html}</body></html>")


    @Slot(bool)
    def update_status(self, is_listening):
        self._is_listening = is_listening
        if is_listening:
            self.status_label.setText("🎤")
            self.status_label.setStyleSheet("color: #00FF00;") # Green
        else:
            self.status_label.setText("👂")
            self.status_label.setStyleSheet("color: #888888;") # Gray

    @Slot(bool)
    def update_pause(self, is_paused):
        self.pause_label.setVisible(is_paused)

    @Slot(bool)
    def set_thinking(self, thinking):
        self._is_thinking = thinking
        if thinking:
            # Only set if not already showing microphone/listening
            if self.status_label.text() not in ["🎤", "📥"]:
                 self.status_label.setText("🌀")
                 self.status_label.setStyleSheet("color: cyan;")
        else:
            if self.status_label.text() == "🌀":
                 self.status_label.setText("👂")
                 self.status_label.setStyleSheet("color: #888888;")
            
    def clear_history(self):
        self.history.clear()
        self.text_label.setText("History cleared.")
        
    @Slot(int)
    def show_loading(self, percent):
        self.status_label.setText("📥")
        self.status_label.setStyleSheet("color: #FFA500;") # Orange
        m_type = self.config.get("model_type", "small")
        model_name = "Preciso (Grande)" if m_type == "big" else "Rápido (Pequeno)"
        text = f"Baixando Modelo {model_name}...\n{percent}%"
        self.text_label.setText(f"<html><body><div style='color: orange;'>{text}</div></body></html>")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()


    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()
