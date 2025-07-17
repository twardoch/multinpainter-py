import pytest
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from PIL import Image
import asyncio

from multinpainter import Multinpainter_OpenAI, __version__
from multinpainter.__main__ import inpaint, describe, get_inpainter


class TestVersioning:
    def test_version_exists(self):
        """Test that version is defined and not unknown"""
        assert __version__ is not None
        assert __version__ != "unknown"
        assert isinstance(__version__, str)


class TestMultinpainterOpenAI:
    def create_test_image(self, size=(512, 512)):
        """Create a test image for testing"""
        image = Image.new('RGB', size, color='red')
        return image

    def test_init_basic(self):
        """Test basic initialization"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            test_image = self.create_test_image()
            test_image.save(tmp.name)
            
            painter = Multinpainter_OpenAI(
                image_path=tmp.name,
                out_path="/tmp/test_out.png",
                out_width=1024,
                out_height=1024
            )
            
            assert painter.image_path == tmp.name
            assert painter.out_path == "/tmp/test_out.png"
            assert painter.out_width == 1024
            assert painter.out_height == 1024
            assert painter.square == 1024  # default value
            assert painter.humans == False  # default value
            assert painter.verbose == False  # default value
            
            os.unlink(tmp.name)

    def test_init_with_params(self):
        """Test initialization with custom parameters"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            test_image = self.create_test_image()
            test_image.save(tmp.name)
            
            painter = Multinpainter_OpenAI(
                image_path=tmp.name,
                out_path="/tmp/test_out.png",
                out_width=1024,
                out_height=1024,
                prompt="test prompt",
                fallback="test fallback",
                square=512,
                step=256,
                humans=True,
                verbose=True,
                openai_api_key="test_key",
                hf_api_key="test_hf_key"
            )
            
            assert painter.prompt == "test prompt"
            assert painter.fallback == "test fallback"
            assert painter.square == 512
            assert painter.step == 256
            assert painter.humans == True
            assert painter.verbose == True
            assert painter.openai_api_key == "test_key"
            
            os.unlink(tmp.name)

    def test_invalid_square_size(self):
        """Test that invalid square sizes raise appropriate errors"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            test_image = self.create_test_image()
            test_image.save(tmp.name)
            
            # Test with an invalid square size
            with pytest.raises((ValueError, AssertionError)):
                Multinpainter_OpenAI(
                    image_path=tmp.name,
                    out_path="/tmp/test_out.png",
                    out_width=1024,
                    out_height=1024,
                    square=100  # Invalid size
                )
            
            os.unlink(tmp.name)

    def test_missing_image_file(self):
        """Test handling of missing image file"""
        with pytest.raises(FileNotFoundError):
            Multinpainter_OpenAI(
                image_path="/nonexistent/path.png",
                out_path="/tmp/test_out.png",
                out_width=1024,
                out_height=1024
            )

    @patch('multinpainter.multinpainter.openai')
    async def test_inpaint_mock(self, mock_openai):
        """Test inpaint method with mocked OpenAI API"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            test_image = self.create_test_image()
            test_image.save(tmp.name)
            
            # Mock the OpenAI API response
            mock_openai.Image.create_edit.return_value = {
                'data': [{'url': 'https://example.com/image.png'}]
            }
            
            with patch('multinpainter.multinpainter.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.content = test_image.tobytes()
                mock_get.return_value = mock_response
                
                painter = Multinpainter_OpenAI(
                    image_path=tmp.name,
                    out_path="/tmp/test_out.png",
                    out_width=600,
                    out_height=600,
                    prompt="test prompt",
                    openai_api_key="test_key"
                )
                
                # This would normally call the API, but we're mocking it
                # The actual test would need more complex mocking
                # For now, just test that the object was created successfully
                assert painter.prompt == "test prompt"
            
            os.unlink(tmp.name)


class TestCLIFunctions:
    def test_get_inpainter(self):
        """Test get_inpainter function"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            test_image = Image.new('RGB', (512, 512), color='red')
            test_image.save(tmp.name)
            
            painter = get_inpainter(
                image_path=tmp.name,
                out_path="/tmp/test_out.png",
                out_width=1024,
                out_height=1024
            )
            
            assert isinstance(painter, Multinpainter_OpenAI)
            assert painter.image_path == tmp.name
            
            os.unlink(tmp.name)

    @patch('multinpainter.__main__.get_inpainter')
    @patch('asyncio.run')
    def test_inpaint_function(self, mock_run, mock_get_inpainter):
        """Test inpaint CLI function"""
        mock_painter = Mock()
        mock_painter.out_path = "/tmp/test_out.png"
        mock_painter.inpaint = AsyncMock()
        mock_get_inpainter.return_value = mock_painter
        
        result = inpaint(
            image="test.png",
            output="/tmp/test_out.png",
            width=1024,
            height=1024,
            prompt="test prompt"
        )
        
        assert result == "/tmp/test_out.png"
        mock_get_inpainter.assert_called_once()
        mock_run.assert_called_once()

    @patch('multinpainter.__main__.get_inpainter')
    @patch('asyncio.run')
    def test_describe_function(self, mock_run, mock_get_inpainter):
        """Test describe CLI function"""
        mock_painter = Mock()
        mock_painter.prompt = "generated description"
        mock_painter.describe_image = AsyncMock()
        mock_get_inpainter.return_value = mock_painter
        
        result = describe(
            image="test.png",
            hf_api_key="test_key"
        )
        
        assert result == "generated description"
        mock_get_inpainter.assert_called_once()
        mock_run.assert_called_once()


class TestIntegration:
    def test_module_imports(self):
        """Test that all expected modules can be imported"""
        from multinpainter import Multinpainter_OpenAI, __version__
        from multinpainter.__main__ import inpaint, describe, cli
        
        # Test that classes and functions exist
        assert Multinpainter_OpenAI is not None
        assert inpaint is not None
        assert describe is not None
        assert cli is not None
        assert __version__ is not None

    def test_entry_point_exists(self):
        """Test that the CLI entry point can be called"""
        from multinpainter.__main__ import cli
        
        # Test that cli function exists and is callable
        assert callable(cli)