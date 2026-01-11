from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox, 
                                 QPushButton, QHBoxLayout, QSlider, QCheckBox, QScrollArea, QWidget, QProgressBar, QMessageBox, QFrame)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
import os
from download_models import setup_vosk, is_model_installed
from core.updater import AppUpdater

class DownloadThread(QThread):
    progress = Signal(int)
    finished = Signal(bool, str)
    
    def __init__(self, model_type):
        super().__init__()
        self.model_type = model_type
        
    def run(self):
        try:
            path, msg = setup_vosk(self.model_type, progress_callback=self.progress.emit)
            if path:
                self.finished.emit(True, f"Modelo {self.model_type} baixado com sucesso!")
            else:
                self.finished.emit(False, f"Falha no download: {msg}")
        except Exception as e:
            self.finished.emit(False, str(e))

class NoWheelComboBox(QComboBox):
    def wheelEvent(self, event):
        # Ignora o scroll para evitar trocas acidentais
        event.ignore()

class NoWheelSlider(QSlider):
    def wheelEvent(self, event):
        # Ignora o scroll no slider
        event.ignore()

class SettingsDialog(QDialog):
    def __init__(self, parent=None, config=None, audio_handler=None, current_version="1.0.0"):
        super().__init__(parent)
        self.setWindowTitle("Configurações - OmniTranslator")
        self.config = config or {}
        self.audio_handler = audio_handler
        self.current_version = current_version
        self.updater = AppUpdater(current_version)
        # Frameless window for custom title bar
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.resize(550, 850)
        self.old_pos = None
        
        # Apply Premium Stylesheet
        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
                color: #E0E0E0;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                color: #B0B0B0;
                font-size: 13px;
                background: transparent;
            }
            QLabel#SectionHeader {
                color: #39FF14;
                font-size: 16px;
                font-weight: bold;
                margin-top: 10px;
                margin-bottom: 5px;
            }
            QLabel#FooterBranding {
                color: #555555;
                font-size: 11px;
                font-style: italic;
            }
            QFrame#Card {
                background-color: #1E1E1E;
                border: 1px solid #333333;
                border-radius: 12px;
            }
            QComboBox {
                background-color: #2D2D2D;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 8px;
                color: white;
                min-width: 150px;
            }
            QComboBox:hover {
                border: 1px solid #39FF14;
            }
            QComboBox::drop-down {
                border: none;
            }
            QSlider::groove:horizontal {
                border: 1px solid #333333;
                height: 6px;
                background: #2D2D2D;
                margin: 2px 0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #39FF14;
                border: 1px solid #39FF14;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #2D2D2D;
                border: 1px solid #444444;
                border-radius: 8px;
                padding: 10px 20px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
                border: 1px solid #39FF14;
            }
            QPushButton#HelpBtn {
                background-color: #2D2D2D;
                border: 1px solid #555555;
                border-radius: 15px;
                padding: 0px;
                min-width: 30px;
                max-width: 30px;
                min-height: 30px;
                max-height: 30px;
                font-size: 18px;
                color: #39FF14;
            }
            QPushButton#SaveBtn {
                background-color: #005F14;
                border: 1px solid #39FF14;
                color: #FFFFFF;
            }
            QPushButton#SaveBtn:hover {
                background-color: #007F19;
            }
            QProgressBar {
                border: 1px solid #333333;
                border-radius: 5px;
                text-align: center;
                background-color: #1E1E1E;
                height: 12px;
                color: white;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #39FF14;
                border-radius: 4px;
            }
            QCheckBox {
                color: #E0E0E0;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #444444;
                background: #2D2D2D;
            }
            QCheckBox::indicator:checked {
                background: #39FF14;
                border: 1px solid #39FF14;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QWidget#ScrollContent {
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #121212;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #333333;
                min-height: 20px;
                border-radius: 5px;
            }
        """)

        main_vbox = QVBoxLayout(self)
        main_vbox.setContentsMargins(0, 0, 0, 0) # No margins for the main container
        main_vbox.setSpacing(0)

        # --- CUSTOM TITLE BAR ---
        title_bar = QFrame()
        title_bar.setObjectName("TitleBar")
        title_bar.setStyleSheet("""
            QFrame#TitleBar {
                background-color: #000000;
                border-bottom: 1px solid #333333;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
            QLabel#TitleText {
                color: #FFFFFF;
                font-size: 13px;
                font-weight: bold;
                padding-left: 15px;
            }
            QPushButton#CloseBtnTitle {
                background-color: transparent;
                border: none;
                color: #FFFFFF;
                font-size: 18px;
                font-weight: bold;
                padding: 5px 15px;
            }
            QPushButton#CloseBtnTitle:hover {
                background-color: #E74C3C;
                color: white;
            }
        """)
        title_bar_lyt = QHBoxLayout(title_bar)
        title_bar_lyt.setContentsMargins(0, 5, 0, 5)
        
        title_lbl = QLabel("Configurações - Hotta Tecnologia")
        title_lbl.setObjectName("TitleText")
        title_bar_lyt.addWidget(title_lbl)
        
        title_bar_lyt.addStretch()
        
        self.close_title_btn = QPushButton("✕")
        self.close_title_btn.setObjectName("CloseBtnTitle")
        self.close_title_btn.clicked.connect(self.reject)
        title_bar_lyt.addWidget(self.close_title_btn)
        
        main_vbox.addWidget(title_bar)

        # Content Container (to have margins)
        content_container = QWidget()
        content_vbox = QVBoxLayout(content_container)
        content_vbox.setContentsMargins(15, 15, 15, 15)
        main_vbox.addWidget(content_container)

        # Header with Help
        header_lyt = QHBoxLayout()
        header_lyt.addWidget(QLabel("<b>HOTTA TECNOLOGIA</b>"))
        header_lyt.addStretch()
        self.help_btn = QPushButton("?")
        self.help_btn.setObjectName("HelpBtn")
        self.help_btn.setToolTip("Ajuda e Instruções")
        self.help_btn.clicked.connect(self.show_help)
        header_lyt.addWidget(self.help_btn)
        content_vbox.addLayout(header_lyt)

        # Scroll Area for long settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content.setObjectName("ScrollContent")
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        scroll.setWidget(content)
        content_vbox.addWidget(scroll)

        # --- AUDIO CARD ---
        audio_card = QFrame()
        audio_card.setObjectName("Card")
        audio_lyt = QVBoxLayout(audio_card)
        audio_lyt.setContentsMargins(20, 20, 20, 20)
        audio_lyt.setSpacing(12)
        
        lbl = QLabel("🎤 ÁUDIO E MICROFONE")
        lbl.setObjectName("SectionHeader")
        audio_lyt.addWidget(lbl)
        
        audio_lyt.addWidget(QLabel("Dispositivo de Entrada:"))
        self.device_combo = NoWheelComboBox()
        self._populate_devices()
        audio_lyt.addWidget(self.device_combo)

        audio_lyt.addWidget(QLabel("Algoritmo de Reconhecimento:"))
        model_row = QHBoxLayout()
        self.model_combo = NoWheelComboBox()
        self.model_combo.addItem("Rápido (Vosk Small)", "small")
        self.model_combo.addItem("Preciso (Vosk Big)", "big")
        self.model_combo.addItem("Ultra (Google Online)", "google")
        curr_model = self.config.get("model_type", "small")
        idx = self.model_combo.findData(curr_model)
        if idx >= 0: self.model_combo.setCurrentIndex(idx)
        model_row.addWidget(self.model_combo)
        
        self.download_btn = QPushButton("Baixar")
        self.download_btn.clicked.connect(self.start_download)
        model_row.addWidget(self.download_btn)
        audio_lyt.addLayout(model_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        audio_lyt.addWidget(self.progress_bar)

        audio_lyt.addWidget(QLabel("Sensibilidade Manual (VAD Threshold):"))
        self.vad_slider = NoWheelSlider(Qt.Horizontal)
        self.vad_slider.setRange(100, 5000)
        self.vad_slider.setValue(int(self.config.get("vad_threshold", 300)))
        audio_lyt.addWidget(self.vad_slider)
        
        # Audio Monitor Section
        monitor_label = QLabel("🎧 Monitor de Áudio em Tempo Real:")
        monitor_label.setStyleSheet("color: #39FF14; font-weight: bold; margin-top: 10px;")
        audio_lyt.addWidget(monitor_label)
        
        # Monitor toggle button
        self.monitor_btn = QPushButton("▶ Iniciar Monitor")
        self.monitor_btn.setCheckable(True)
        self.monitor_btn.clicked.connect(self._toggle_monitor)
        audio_lyt.addWidget(self.monitor_btn)
        
        # Energy level display
        self.energy_bar = QProgressBar()
        self.energy_bar.setRange(0, 5000)
        self.energy_bar.setValue(0)
        self.energy_bar.setTextVisible(True)
        self.energy_bar.setFormat("Energia: %v | Threshold: " + str(int(self.config.get("vad_threshold", 300))))
        audio_lyt.addWidget(self.energy_bar)
        
        # Update energy bar format when slider changes
        self.vad_slider.valueChanged.connect(lambda v: self.energy_bar.setFormat(f"Energia: %v | Threshold: {v}"))
        
        # Monitoring state
        self.monitoring = False
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._update_energy_display)
        
        layout.addWidget(audio_card)

        # --- UPDATE & ABOUT CARD ---
        update_card = QFrame()
        update_card.setObjectName("Card")
        update_lyt = QVBoxLayout(update_card)
        
        header = QLabel("🌍 SOBRE E ATUALIZAÇÕES")
        header.setObjectName("SectionHeader")
        update_lyt.addWidget(header)
        
        info_lyt = QHBoxLayout()
        v_label = QLabel(f"Versão Atual: <b>{self.current_version}</b>")
        info_lyt.addWidget(v_label)
        
        self.check_update_btn = QPushButton("Verificar Atualizações")
        self.check_update_btn.setMinimumHeight(35)
        self.check_update_btn.clicked.connect(self._check_for_updates)
        info_lyt.addWidget(self.check_update_btn)
        update_lyt.addLayout(info_lyt)
        
        # Progress for update download
        self.update_progress = QProgressBar()
        self.update_progress.setVisible(False)
        update_lyt.addWidget(self.update_progress)
        
        layout.addWidget(update_card)

        # --- TRANSLATION CARD ---
        trans_card = QFrame()
        trans_card.setObjectName("Card")
        trans_lyt = QVBoxLayout(trans_card)
        trans_lyt.setContentsMargins(20, 20, 20, 20)
        trans_lyt.setSpacing(12)
        
        lbl = QLabel("🌍 TRADUÇÃO E IDIOMA")
        lbl.setObjectName("SectionHeader")
        trans_lyt.addWidget(lbl)
        
        trans_lyt.addWidget(QLabel("Traduzir para:"))
        self.lang_combo = NoWheelComboBox()
        langs = [
            ("Inglês", "en"), ("Espanhol", "es"), ("Francês", "fr"), 
            ("Alemão", "de"), ("Italiano", "it"), ("Japonês", "ja"), ("Chinês", "zh-CN")
        ]
        for name, code in langs:
            self.lang_combo.addItem(name, code)
        curr_lang = self.config.get("target_lang", "en")
        idx = self.lang_combo.findData(curr_lang)
        if idx >= 0: self.lang_combo.setCurrentIndex(idx)
        trans_lyt.addWidget(self.lang_combo)
        
        layout.addWidget(trans_card)

        # --- VISUAL CARD ---
        visual_card = QFrame()
        visual_card.setObjectName("Card")
        visual_lyt = QVBoxLayout(visual_card)
        visual_lyt.setContentsMargins(20, 20, 20, 20)
        visual_lyt.setSpacing(12)
        
        lbl = QLabel("✨ VISUAL E INTERFACE")
        lbl.setObjectName("SectionHeader")
        visual_lyt.addWidget(lbl)
        
        visual_lyt.addWidget(QLabel("Largura do Painel:"))
        self.width_slider = NoWheelSlider(Qt.Horizontal)
        self.width_slider.setRange(400, 1920)
        self.width_slider.setValue(self.config.get("win_width", 1000))
        visual_lyt.addWidget(self.width_slider)
        
        visual_lyt.addWidget(QLabel("Altura do Painel:"))
        self.height_slider = NoWheelSlider(Qt.Horizontal)
        self.height_slider.setRange(100, 600)
        self.height_slider.setValue(self.config.get("win_height", 240))
        visual_lyt.addWidget(self.height_slider)

        visual_lyt.addWidget(QLabel("Alinhamento do Texto:"))
        self.align_combo = NoWheelComboBox()
        self.align_combo.addItem("Topo", "top")
        self.align_combo.addItem("Meio", "center")
        self.align_combo.addItem("Baixo", "bottom")
        curr_align = self.config.get("text_align", "top")
        idx = self.align_combo.findData(curr_align)
        if idx >= 0: self.align_combo.setCurrentIndex(idx)
        visual_lyt.addWidget(self.align_combo)

        visual_lyt.addWidget(QLabel("Transparência do Fundo:"))
        self.opacity_slider = NoWheelSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(int(self.config.get("opacity", 0.7) * 100))
        visual_lyt.addWidget(self.opacity_slider)
        
        visual_lyt.addWidget(QLabel("Cor da Tradução:"))
        self.trans_color_combo = NoWheelComboBox()
        colors = [
            ("Verde Neon", "#39FF14"), ("Amarelo Sol", "yellow"), ("Ciano", "cyan"), 
            ("Branco Puro", "white"), ("Laranja Vivo", "orange")
        ]
        for name, code in colors:
            self.trans_color_combo.addItem(name, code)
        curr_t_color = self.config.get("trans_color", "#39FF14")
        idx = self.trans_color_combo.findData(curr_t_color)
        if idx >= 0: self.trans_color_combo.setCurrentIndex(idx)
        visual_lyt.addWidget(self.trans_color_combo)
        
        visual_lyt.addWidget(QLabel("Tamanho da Fonte (Tradução):"))
        self.trans_font_slider = NoWheelSlider(Qt.Horizontal)
        self.trans_font_slider.setRange(14, 72)
        self.trans_font_slider.setValue(self.config.get("trans_font_size", 24))
        visual_lyt.addWidget(self.trans_font_slider)

        self.top_check = QCheckBox("Manter sempre visível sobre outros apps")
        self.top_check.setChecked(self.config.get("always_on_top", True))
        visual_lyt.addWidget(self.top_check)

        layout.addWidget(visual_card)

        # Footer Branding
        footer_branding = QLabel("© 2026 Hotta Tecnologia - Todos os direitos reservados.")
        footer_branding.setObjectName("FooterBranding")
        footer_branding.setAlignment(Qt.AlignCenter)
        main_vbox.addWidget(footer_branding)

        # Footer Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 5, 0, 5)
        btn_layout.setSpacing(15)
        
        self.save_btn = QPushButton("SALVAR ALTERAÇÕES")
        self.save_btn.setObjectName("SaveBtn")
        self.save_btn.clicked.connect(self.save_settings)
        
        self.cancel_btn = QPushButton("CANCELAR")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.save_btn, 2)
        btn_layout.addWidget(self.cancel_btn, 1)
        content_vbox.addLayout(btn_layout)

        # Connect model change for download button
        self.model_combo.currentIndexChanged.connect(self._update_download_btn_visibility)
        self._update_download_btn_visibility()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def show_help(self):
        help_text = """
        <div style='font-family: Segoe UI, sans-serif;'>
            <h2 style='color: #39FF14; border-bottom: 2px solid #39FF14; padding-bottom: 5px;'>Guia de Operação - Hotta Tecnologia</h2>
            
            <p style='color: #FFF;'><b>Controles Globais:</b></p>
            <ul style='color: #B0B0B0;'>
                <li><b style='color: #39FF14;'>CTRL + ALT + S:</b> Iniciar / Pausar a captura de áudio.</li>
                <li><b style='color: #39FF14;'>CTRL + ALT + C:</b> Limpar o histórico de legendas da tela.</li>
                <li><b>Arrastar:</b> Clique em qualquer lugar da legenda para reposicioná-la.</li>
            </ul>

            <p style='color: #FFF;'><b>Motores de Reconhecimento:</b></p>
            <ul style='color: #B0B0B0;'>
                <li><b style='color: #FFF;'>Vosk (Offline):</b> Rápido e privado. Não requer internet. Ideal para PCs mais modestos.</li>
                <li><b style='color: #FFF;'>Ultra (Google Online):</b> Máxima precisão. Utiliza nossos filtros de isolamento de ruído estúdio e inteligência contextual da Google.</li>
            </ul>

            <p style='color: #FFF;'><b>Perfis de Detecção (VAD):</b></p>
            <ul style='color: #B0B0B0;'>
                <li><b style='color: #39FF14;'>Sensível:</b> Para lugares bem silenciosos. Detecta até quem fala baixo, mas pode pegar ruídos de fundo leves.</li>
                <li><b style='color: #39FF14;'>Balanceado:</b> O equilíbrio ideal para a maioria das pessoas e microfones.</li>
                <li><b style='color: #39FF14;'>Robusto:</b> Ideal se você tem ventilador, teclado barulhento ou música ao fundo. Ele ignora mais os ruídos, mas exige que você fale um pouco mais firme.</li>
            </ul>

            <hr style='border: 0; border-top: 1px solid #333;'>
            <p style='color: #555; font-size: 10px; text-align: center;'>Versão Premium | Desenvolvido por Hotta Tecnologia</p>
        </div>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("Centro de Ajuda - Hotta Tecnologia")
        msg.setTextFormat(Qt.RichText)
        msg.setText(help_text)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #121212;
            }
            QLabel {
                color: #B0B0B0;
            }
            QPushButton {
                background-color: #2D2D2D;
                color: white;
                border: 1px solid #444444;
                padding: 5px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
                border: 1px solid #00FFCC;
            }
        """)
        msg.exec()

    def start_download(self):
        m_type = self.model_combo.currentData()
        if m_type == "google":
            QMessageBox.information(self, "Google Mode", "O modo Google Online não precisa de download.")
            return

        self.download_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.dl_thread = DownloadThread(m_type)
        self.dl_thread.progress.connect(self.progress_bar.setValue)
        self.dl_thread.finished.connect(self.finish_download)
        self.dl_thread.start()

    def finish_download(self, success, message):
        self.download_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        if success:
            QMessageBox.information(self, "Download Concluído", message)
            self._update_download_btn_visibility()
        else:
            QMessageBox.critical(self, "Erro no Download", message)

    def _update_download_btn_visibility(self):
        m_type = self.model_combo.currentData()
        installed = is_model_installed(m_type)
        self.download_btn.setVisible(not installed)

    def _populate_devices(self):
        if not self.audio_handler:
            self.device_combo.addItem("Audio não disponível")
            return
        devices = self.audio_handler.get_devices()
        current_index = self.config.get("audio_device_index", -1)
        for dev in devices:
            self.device_combo.addItem(dev['name'], dev['index'])
        idx = self.device_combo.findData(current_index)
        if idx >= 0: self.device_combo.setCurrentIndex(idx)

    def _toggle_monitor(self):
        """Toggle real-time audio monitoring"""
        self.monitoring = not self.monitoring
        
        if self.monitoring:
            self.monitor_btn.setText("⏸ Parar Monitor")
            self.monitor_btn.setStyleSheet("background-color: #E74C3C; border-color: #E74C3C;")
            self.monitor_timer.start(50)  # Update every 50ms
        else:
            self.monitor_btn.setText("▶ Iniciar Monitor")
            self.monitor_btn.setStyleSheet("")
            self.monitor_timer.stop()
            self.energy_bar.setValue(0)
    
    def _update_energy_display(self):
        """Update energy level display from audio handler"""
        if not self.audio_handler or not self.monitoring:
            return
        
        try:
            # Get current audio energy from the audio queue
            audio_data = self.audio_handler.get_audio()
            if audio_data:
                _, _, energy = audio_data
                self.energy_bar.setValue(int(energy))
                
                # Visual feedback: change color if above threshold
                threshold = self.vad_slider.value()
                if energy > threshold:
                    # Above threshold - detected as speech
                    self.energy_bar.setStyleSheet("""
                        QProgressBar::chunk {
                            background-color: #39FF14;
                        }
                    """)
                else:
                    # Below threshold - not detected
                    self.energy_bar.setStyleSheet("""
                        QProgressBar::chunk {
                            background-color: #555555;
                        }
                    """)
        except Exception as e:
            pass  # Silently ignore queue errors

    def _check_for_updates(self):
        """Standard GitHub check"""
        self.check_update_btn.setEnabled(False)
        self.check_update_btn.setText("Verificando...")
        
        # We can do this in a thread later if it blocks too much, but for now GitHub API is fast
        has_update, latest_v, url = self.updater.check_for_updates()
        
        if has_update:
            reply = QMessageBox.question(self, "Atualização Disponível", 
                                        f"Uma nova versão ({latest_v}) está disponível.\nDeseja baixar e atualizar agora?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self._start_update_download(url)
            else:
                self.check_update_btn.setEnabled(True)
                self.check_update_btn.setText("Verificar Atualizações")
        else:
            if latest_v:
                QMessageBox.information(self, "OmniTranslator", f"Você já está na versão mais recente ({self.current_version}).")
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível verificar atualizações. Verifique sua conexão.")
            self.check_update_btn.setEnabled(True)
            self.check_update_btn.setText("Verificar Atualizações")

    def _start_update_download(self, url):
        self.update_progress.setVisible(True)
        self.update_progress.setValue(0)
        self.check_update_btn.setText("Baixando...")
        
        # Using a QThread for download to not freeze UI
        class UpdaterThread(QThread):
            progress = Signal(int)
            finished = Signal(bool)
            def __init__(self, updater, url):
                super().__init__()
                self.updater = updater
                self.url = url
            def run(self):
                success = self.updater.download_and_apply(self.url, self.progress.emit)
                self.finished.emit(success)

        self.up_thread = UpdaterThread(self.updater, url)
        self.up_thread.progress.connect(self.update_progress.setValue)
        self.up_thread.finished.connect(self._finish_update)
        self.up_thread.start()

    def _finish_update(self, success):
        self.update_progress.setVisible(False)
        if success:
            QMessageBox.information(self, "Pronto!", "A atualização foi baixada. O programa irá reiniciar agora.")
            self.updater.restart_and_update()
        else:
            QMessageBox.critical(self, "Erro", "Falha ao baixar a atualização.")
            self.check_update_btn.setEnabled(True)
            self.check_update_btn.setText("Verificar Atualizações")

    def save_settings(self):
        self.config["win_width"] = self.width_slider.value()
        self.config["win_height"] = self.height_slider.value()
        self.config["opacity"] = self.opacity_slider.value() / 100.0
        self.config["audio_device_index"] = self.device_combo.currentData()
        self.config["model_type"] = self.model_combo.currentData()
        self.config["target_lang"] = self.lang_combo.currentData()
        self.config["vad_threshold"] = self.vad_slider.value()
        self.config["trans_color"] = self.trans_color_combo.currentData()
        self.config["trans_font_size"] = self.trans_font_slider.value()
        self.config["always_on_top"] = self.top_check.isChecked()
        self.config["text_align"] = self.align_combo.currentData()
        self.accept()
