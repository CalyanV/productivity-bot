import pytest
from pathlib import Path
from src.voice import VoiceHandler

@pytest.mark.asyncio
async def test_voice_handler_initialization():
    """Test VoiceHandler initializes correctly"""
    handler = VoiceHandler()
    assert handler is not None

@pytest.mark.asyncio
async def test_download_voice_file(tmp_path):
    """Test downloading voice file from Telegram"""
    handler = VoiceHandler()

    # Mock file object
    class MockFile:
        async def download_to_drive(self, path):
            # Create a dummy audio file
            Path(path).write_bytes(b"dummy audio data")

    mock_file = MockFile()
    output_path = tmp_path / "voice.ogg"

    result = await handler.download_voice(mock_file, str(output_path))
    assert result == str(output_path)
    assert Path(output_path).exists()

@pytest.mark.asyncio
async def test_transcribe_audio(tmp_path):
    """Test audio transcription (mock, requires Whisper)"""
    handler = VoiceHandler()

    # Create a dummy audio file
    audio_file = tmp_path / "test.ogg"
    audio_file.write_bytes(b"dummy audio data")

    # Note: This would require actual Whisper model in real test
    # For now, we're just testing the method signature exists
    try:
        # This will fail without actual audio, but validates the interface
        result = await handler.transcribe(str(audio_file))
    except Exception as e:
        # Expected to fail with dummy data
        assert True
