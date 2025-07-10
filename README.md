# Mini Ollama （AI Power）[中文](https://github.com/hengruiyun/Mini-Ollama/blob/main/README_CN.md)

## Acknowledgments

**Special thanks to the [Ollama Team](https://github.com/ollama/ollama) for creating this amazing AI platform!**

This project is built upon the foundation of Ollama, an incredible open-source platform that makes running AI models locally accessible to everyone. Without their innovative work, MiniOllama would not exist. We are grateful for their dedication to democratizing AI technology and making it available to developers and users worldwide.

---

A revolutionary lightweight GUI for running powerful AI models completely CPU-only - no GPU required! Perfect for any Windows computer, from budget laptops to enterprise workstations.

<img width="1040" height="807" alt="mO-1" src="https://github.com/user-attachments/assets/cfe28cac-fcea-41b1-b088-8079db617f27" />

## Key Features

### **Revolutionary CPU-Only AI - No GPU Required!**
- **Zero GPU Dependency**: Run powerful large language models using only your CPU - no expensive graphics cards needed!
- **Universal Compatibility**: Works on ANY Windows computer - from 5-year-old laptops to modern workstations
- **Instant Setup**: No CUDA drivers, no GPU compatibility checks - just install and run

### **Democratizing Large Language Models**
- **Accessible AI for Everyone**: Bring enterprise-grade AI capabilities to every computer owner
- **No Hardware Barriers**: Students, researchers, and developers can experiment with AI regardless of their hardware budget
- **Small Business Ready**: Enable AI features in small businesses without infrastructure investment
- **Offline Intelligence**: Complete AI functionality without internet dependency or cloud costs
- **Privacy First**: Your data never leaves your computer - complete privacy and security

### **Complete Ollama Management**
- **Auto-start Configuration**: Automatically start Ollama service on boot
- **Model Management**: Download, delete, and manage AI models
- **Chat Interface**: Built-in chat interface for testing models
- **Bilingual Support**: Automatic language detection (English/Chinese)

### **User-Friendly Design**
- **Modern GUI**: Clean, intuitive interface built with Tkinter
- **Real-time Status**: Live service status and connection monitoring
- **Progress Tracking**: Visual progress bars for model downloads


## Performance Data - Proof That CPU-Only AI Works!

| Metric | Value | Description |
|--------|-------|-------------|
| **GPU Requirement** | **ZERO** | **No graphics card needed - runs on integrated graphics!** |
| **CPU Support** | Any x64 | Intel, AMD, even older processors work perfectly |
| **Startup Time** | <3 seconds | Instant AI access without lengthy GPU initialization |
| **Model Size** | 0.5-1.5GB | Compact yet powerful models optimized for CPU inference |
| **Minimum RAM** | 4GB | Recommended for smooth large model operation |


## Use Cases - CPU-Only AI Revolution

### **Perfect For Everyone Without Expensive Hardware:**
- **Budget-Conscious Developers**: Build AI applications without $2000+ GPU investments
- **Students & Researchers**: Access powerful language models on university/personal laptops
- **Small Businesses**: Implement AI customer service, content generation, and automation affordably
- **Content Creators**: Generate articles, code, and creative content using only your existing computer
- **Privacy-Focused Users**: Keep sensitive data local while enjoying AI assistance
- **Educational Institutions**: Teach AI concepts without expensive lab equipment
- **Remote Workers**: AI-powered productivity tools that work anywhere, even offline
- **Hobbyist Programmers**: Experiment with cutting-edge AI on weekend projects
- **Legacy Hardware Users**: Breathe new AI life into older computers
- **Quiet Environments**: Libraries, shared offices, bedrooms - no noisy GPU cooling

### **Real-World CPU-Only AI Applications:**
- **Code Assistant**: Get programming help, debug code, explain algorithms
- **Writing Companion**: Generate articles, emails, creative writing, documentation
- **Language Translator**: Translate text between languages completely offline
- **Research Assistant**: Summarize documents, answer questions, analyze data
- **Learning Tutor**: Get explanations on complex topics, practice conversations
- **Business Automation**: Generate reports, analyze feedback, create proposals

### **Not Recommended For:**
- Real-time video processing with large models
- Training new models from scratch (inference only)
- Extremely time-sensitive applications requiring sub-second responses


## Quick Start

### Prerequisites - No GPU Required!
- **CPU**: Any 64-bit processor (Intel/AMD) - even older models work!
- **GPU**: **NOT REQUIRED** - integrated graphics are sufficient
- **OS**: Windows 10/11 (64-bit)
- **Runtime**: Python 3.10 or higher
- **RAM**: 4GB+ (8GB recommended for larger models)
- **Storage**: 5GB+ free disk space (for AI models)
- **Graphics**: Basic integrated graphics (no dedicated GPU needed)
- **Power**: Standard laptop/desktop power supply (no high-wattage PSU required)

### Installation

1. **Download MiniOllama**
   ```bash
   MiniOllamaSetup.exe
   ```

2. **Run the Application**
   ```bash
   MiniOllama.exe
   ```

### First Time Setup

1. **Download Your First Model**
   - Go to "Model Management" tab
   - Select a lightweight model (e.g., `tinyllama:1.1b` - 0.6GB)
   - Click "Download Selected Model"
   - Wait for download completion

2. **Test the Model**
   - Switch to "Chat Interface" tab
   - Select your downloaded model
   - Type a message and click "Send"

3. **Configure Auto-start** (Optional)
   - Navigate to "Auto Start" tab
   - Enable "Auto start Ollama service on boot"
   - Click "Save Settings"


## Recommended Models

| Model | Size | Use Case | Performance |
|-------|------|----------|-------------|
| `tinyllama:1.1b` | 0.6GB | Basic chat, learning | Fast, low resource |
| `qwen3:0.6b` | 0.5GB | Lightweight tasks | Very fast |
| `gemma3:1b` | 0.8GB | General purpose | Balanced |
| `deepseek-r1:1.5b` | 1.1GB | Code assistance | Good reasoning |
| `llama3.2:1b` | 1.3GB | Advanced chat | Best quality |


## Configuration

### Environment Variables
The application manages these Ollama environment variables:

- **OLLAMA_HOST**: Server address (default: localhost)
- **OLLAMA_PORT**: Port number (default: 11434)
- **OLLAMA_MODELS**: Model storage path (default: ~/.ollama/models)
- **OLLAMA_KEEP_ALIVE**: Model keep-alive time (default: 5m)



## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.


## Support

### Getting Help
- Email：267278466@qq.com

---

**MiniOllama** - Making AI accessible on any Windows computer! 🚀

*Perfect for development, learning, and low-resource environments.* 
