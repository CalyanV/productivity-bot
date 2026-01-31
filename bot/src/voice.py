import whisper
import logging
from pathlib import Path
from typing import Optional
import asyncio
import os

logger = logging.getLogger(__name__)


class VoiceHandler:
    """Handle voice message transcription using Whisper"""

    def __init__(self, model_name: str = "base"):
        """
        Initialize voice handler with Whisper model

        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
                       base is good balance of speed/accuracy
        """
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        """Lazy load Whisper model"""
        if self._model is None:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self._model = whisper.load_model(self.model_name)
            logger.info("Whisper model loaded")
        return self._model

    async def download_voice(self, telegram_file, output_path: str) -> str:
        """
        Download voice file from Telegram

        Args:
            telegram_file: Telegram File object
            output_path: Path to save the file

        Returns:
            Path to downloaded file
        """
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Download file
        await telegram_file.download_to_drive(output_path)
        logger.info(f"Downloaded voice file to: {output_path}")

        return output_path

    async def transcribe(self, audio_path: str, language: Optional[str] = None) -> str:
        """
        Transcribe audio file using Whisper

        Args:
            audio_path: Path to audio file
            language: Optional language code (e.g., 'en', 'es')
                     If None, Whisper will auto-detect

        Returns:
            Transcribed text
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Load model
        model = self._load_model()

        # Run transcription in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: model.transcribe(
                audio_path,
                language=language,
                fp16=False  # Use FP32 for CPU compatibility
            )
        )

        text = result["text"].strip()
        detected_language = result.get("language", "unknown")

        logger.info(f"Transcribed audio ({detected_language}): {text[:100]}...")
        return text

    async def process_voice_message(
        self,
        telegram_file,
        temp_dir: str = "/tmp/voice_messages"
    ) -> dict:
        """
        Complete voice message processing pipeline

        Args:
            telegram_file: Telegram File object
            temp_dir: Directory for temporary files

        Returns:
            Dictionary with transcription and metadata
        """
        # Create temp directory
        Path(temp_dir).mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        import uuid
        file_id = str(uuid.uuid4())
        audio_path = f"{temp_dir}/{file_id}.ogg"

        try:
            # Download voice message
            await self.download_voice(telegram_file, audio_path)

            # Transcribe
            text = await self.transcribe(audio_path)

            # Get file info
            file_size = Path(audio_path).stat().st_size

            return {
                "success": True,
                "text": text,
                "file_size": file_size,
                "audio_path": audio_path
            }

        except Exception as e:
            logger.error(f"Error processing voice message: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "audio_path": audio_path if Path(audio_path).exists() else None
            }

    def cleanup_temp_file(self, file_path: str):
        """Remove temporary audio file"""
        try:
            if Path(file_path).exists():
                os.remove(file_path)
                logger.debug(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {file_path}: {e}")
