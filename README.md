# MiniAI (AI Intelligence)

A revolutionary lightweight AI that can run powerful AI models entirely on CPU - no GPU required! Perfect for any computer, from lightweight laptops to enterprise machines.

## Core Features

### **Revolutionary Pure CPU AI - No GPU Required!**
- **Zero GPU Dependency**: Run powerful large language models using only CPU - no expensive graphics cards needed!
- **Universal Compatibility**: Works on any computer - from 10-year-old laptops to modern machines
- **Plug and Play**: No CUDA drivers, no GPU compatibility checks - install and run immediately

### **Democratizing Large Language Models**
- **AI for Everyone**: Bringing enterprise-grade AI capabilities to every computer user
- **No Hardware Barriers**: Students, researchers, and developers can experience AI regardless of hardware budget
- **Small Business Ready**: Enable AI functionality for small businesses without infrastructure investment
- **Offline Intelligence**: Complete AI functionality without internet dependency or cloud service fees

### **Complete Ollama Management**
- **Auto-start Configuration**: Automatically start Ollama service on boot
- **Model Management**: Download, delete, and manage AI models
- **Chat Interface**: Built-in chat interface for testing models

### **🚀 Intelligent Auto Web Search - Revolutionary AI Enhancement!**
- **Smart Confidence Detection**: Automatically evaluates AI response quality and reliability
- **Automatic Web Enhancement**: When confidence is low (<70%), automatically searches the web for accurate information
- **Real-time Information**: Get up-to-date information for time-sensitive queries
- **Seamless Integration**: Web search results are intelligently merged with AI responses
- **No Manual Intervention**: Fully automated - just ask questions and get enhanced answers
- **Multi-source Verification**: Combines multiple web sources for comprehensive responses

## Performance Data - Pure CPU AI Running Proof!

| Metric | Value | Description |
|--------|-------|-------------|
| **GPU Requirement** | **Zero** | **No graphics card needed - integrated graphics sufficient!** |
| **CPU Support** | Any x64 | Intel, AMD, even older processors run perfectly |
| **Startup Time** | <3 seconds | No lengthy GPU initialization, instant AI access |
| **Model Size** | 0.2-2.5GB | Compact yet powerful models optimized for CPU inference |
| **Minimum RAM** | 4GB | Recommended for smooth large model operation |

## Use Cases - Pure CPU AI Revolution

### **Perfect for All Users Without Expensive Hardware:**
- **Budget Developers**: Build AI applications without investing $20,000 in GPUs
- **Students and Researchers**: Access powerful language models on university/personal laptops
- **Small Businesses**: Economically implement AI customer service, content generation, and automation
- **Content Creators**: Generate articles, code, and creative content using existing computers only
- **Educational Institutions**: Teach AI concepts without expensive lab equipment
- **Remote Workers**: AI productivity tools available anywhere, even offline
- **Legacy Hardware Users**: Breathe new AI life into older computers
- **Quiet Environments**: Libraries, shared offices, bedrooms - no noisy GPU cooling

### **🌐 Enhanced with Auto Web Search:**
- **Research Assistance**: Get current information for academic papers and reports
- **News and Updates**: Always get the latest information on current events
- **Technical Support**: Automatically fetch up-to-date documentation and solutions
- **Market Research**: Real-time data for business decisions and analysis
- **Fact Checking**: Automatic verification of information with web sources
- **Learning Enhancement**: Get comprehensive answers with multiple perspectives

### **Not Recommended For:**
- Large model real-time video processing
- Training new models from scratch (inference only)
- Ultra-time-sensitive applications requiring sub-second responses

## Quick Start

### Prerequisites - No GPU Required!
- **CPU**: Any 64-bit processor (Intel/AMD) - even older models work!
- **GPU**: **Not needed** - integrated graphics sufficient
- **Operating System**: Windows 10/11 (64-bit)
- **Runtime**: Python 3.10 or higher
- **Memory**: 4GB+ (8GB recommended for larger models)
- **Storage**: 5GB+ available disk space (for AI models)
- **Graphics**: Basic integrated graphics (no dedicated GPU required)
- **Power**: Standard laptop/desktop power supply (no high-wattage PSU needed)

### Installation

1. **Download MiniAI One-Click Installer**
   ```bash
   MiniAISetup.exe
   ```
2. **Run the Application**
   ```bash
   MiniAI.exe
   ```

### First-Time Setup

1. **Download Your First Model**
   - Go to "Model Management" tab
   - Select a lightweight model (e.g., `qwen3:0.6b`)
   - Click "Download Model"
   - Wait for download completion

2. **Test the Model**
   - Switch to "Chat Interface" tab
   - Select your downloaded model
   - Type a message and click "Send"

3. **Configure Auto-start** (Optional)
   - Switch to "Auto-start" tab
   - Enable "Auto-start Ollama service on boot"

## Recommended Models

| Model | Size | Use Case | Performance |
|-------|------|----------|-------------|
| `tinyllama:1.1b` | 0.6GB | Basic chat, learning | Fast, low resource |
| `qwen3:0.6b` | 0.5GB | Lightweight tasks | Very fast |
| `gemma3:1b` | 0.8GB | General purpose | Balanced |
| `deepseek-r1:1.5b` | 1.1GB | Code assistance | Good reasoning |
| `llama3.2:1b` | 1.3GB | Code assistance | Good reasoning |
| `qwen3:4b` | 2.5GB | Advanced chat | Best quality |

## Configuration

### Environment Variables
The application manages these Ollama environment variables:

- **OLLAMA_HOST**: Server address (default: localhost)
- **OLLAMA_PORT**: Port number (default: 11434)
- **OLLAMA_MODELS**: Model storage path (default: ~/.ollama/models)
- **OLLAMA_KEEP_ALIVE**: Model keep-alive time (default: 5m)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

### Getting Help
- Email: 267278466@qq.com

---

## Acknowledgments

**Special thanks to the [Ollama team](https://github.com/ollama/ollama) for creating this amazing AI platform!**

This project is built on top of Ollama, an incredible open-source platform that makes it possible for everyone to run AI models locally. Without the innovative work of the Ollama team, MiniAI would not exist. We appreciate their dedication to AI technology and making it accessible to developers and users worldwide.

Thanks to the [MCP Server Freesearch](https://github.com/wzj177/mcp-server-freesearch) provided a search platform

---

**MiniAI** - Making AI accessible on any Windows computer! 🚀

*Designed for development, learning, and low-resource environments.*
