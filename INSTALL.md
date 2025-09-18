# Installation Guide - MCP Ctags Server

A standalone MCP server for ctags-based code navigation in Claude Code.

## Quick Install

### Option 1: Install from PyPI (when published)
```bash
pip install ctags-mcp
```

### Option 2: Install from Source
```bash
git clone <repository-url>
cd ctags-mcp
pip install .
```

### Option 3: Development Install
```bash
git clone <repository-url>
cd ctags-mcp
pip install -e .
```

## Prerequisites

1. **Python Requirements**:
   - Python 3.10 or higher
   - pip or uv package manager

2. **Ctags Installation**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install universal-ctags

   # macOS with Homebrew
   brew install universal-ctags

   # Windows (with Chocolatey)
   choco install universal-ctags
   ```

3. **Generate Tags File**:
   ```bash
   # In your project directory
   ctags -R --exclude=node_modules --exclude=.git .
   ```

## Claude Desktop Integration

1. **Find your Claude Desktop config file**:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/claude/claude_desktop_config.json`

2. **Add the MCP server configuration**:
   ```json
   {
     "mcpServers": {
       "ctags": {
         "command": "ctags-mcp"
       }
     }
   }
   ```

   Or for a specific working directory:
   ```json
   {
     "mcpServers": {
       "ctags": {
         "command": "ctags-mcp",
         "args": ["--working-dir", "/path/to/your/project"]
       }
     }
   }
   ```

3. **Restart Claude Desktop**

## Auto-Regeneration (Recommended)

Keep your tags file automatically updated when code changes:

1. **Copy the auto-regeneration configuration**:
   ```bash
   cp .claude/settings.json /path/to/your/project/.claude/
   ```

2. **Or create manually** in your project root:
   ```bash
   mkdir -p .claude
   cat > .claude/settings.json << 'EOF'
   {
     "hooks": {
       "PostToolUse": [
         {
           "matcher": "Edit|MultiEdit|Write",
           "hooks": [
             {
               "type": "command",
               "command": "ctags -R --exclude=__pycache__ --exclude=.git --exclude=.venv ."
             }
           ]
         }
       ]
     }
   }
   EOF
   ```

**[🔄 See AUTO_REGENERATION.md for detailed configuration](AUTO_REGENERATION.md)**

## Verification

1. **Test the CLI**:
   ```bash
   ctags-mcp --help
   ctags-mcp --version
   ```

2. **Test with tags file**:
   ```bash
   # In a directory with a tags file
   ctags-mcp --working-dir .
   ```

3. **Check Claude Desktop**:
   - Open Claude Desktop
   - Look for "ctags" in available MCP servers
   - Try asking: "Find all async functions in this project"

## Troubleshooting

### Command not found: ctags-mcp
- Ensure the package is installed: `pip list | grep ctags-mcp`
- Check your PATH includes pip/uv bin directory
- Try: `python -m ctags_mcp.main --help`

### No ctags file found
- Generate tags file: `ctags -R .`
- Verify file exists: `ls -la tags .tags TAGS`
- Check working directory is correct

### MCP server not responding
- Test CLI directly: `ctags-mcp --help`
- Check Claude Desktop config syntax
- Restart Claude Desktop after config changes
- Check Claude Desktop logs for errors

### Permission errors
- Ensure ctags file is readable
- Check directory permissions
- Try running with explicit working directory

## Advanced Configuration

### Custom Transport (future)
```bash
ctags-mcp --transport stdio  # Current default
```

### Multiple Projects
```json
{
  "mcpServers": {
    "ctags-project1": {
      "command": "ctags-mcp",
      "args": ["--working-dir", "/path/to/project1"]
    },
    "ctags-project2": {
      "command": "ctags-mcp",
      "args": ["--working-dir", "/path/to/project2"]
    }
  }
}
```

### Performance Tuning
- Keep tags files under 10,000 entries for best performance
- Exclude unnecessary directories: `ctags -R --exclude=node_modules --exclude=.git --exclude=build .`
- Regenerate tags periodically: `ctags -R .`

