# Demo GIF Placeholder

## Recording Instructions

To create the 90-second demo GIF, record the following workflow:

### Setup
1. Start the application: `docker compose up -d`
2. Run seed script: `./scripts/seed_demo.sh`
3. Open browser to `http://localhost:8000/`

### Recording Steps (90 seconds)
1. **[0-10s]** Show the homepage loading with welcome message
2. **[10-25s]** Upload `docs/sample_knowledge.txt` file
   - Click "Choose File"
   - Select the sample file
   - Click "Upload"
   - Show success message
3. **[25-45s]** Ask knowledge-based question
   - Type: "What are the key components of a data flywheel?"
   - Click "Send" or press Enter
   - Show AI response with knowledge sources
4. **[45-60s]** Provide feedback
   - Click 👍 button on the response
   - Add comment: "Great explanation!"
   - Show success confirmation
5. **[60-75s]** Load chat history
   - Click "Load Recent" button
   - Show conversation history loading
6. **[75-90s]** Ask follow-up question
   - Type: "How do chatbots contribute to data flywheels?"
   - Show response with source attribution

### Recording Tools
- **macOS:** QuickTime Player (File → New Screen Recording)
- **Windows:** Xbox Game Bar (Win + G)
- **Linux:** OBS Studio or SimpleScreenRecorder
- **Online:** Loom, Screencastify

### GIF Conversion
```bash
# Using ffmpeg to convert video to GIF
ffmpeg -i demo_recording.mp4 -vf "fps=10,scale=800:-1:flags=lanczos" -t 90 docs/demo.gif

# Or use online converters:
# - ezgif.com
# - cloudconvert.com
```

### File Specifications
- **Duration:** 90 seconds maximum
- **Resolution:** 800px width (height auto)
- **Frame Rate:** 10 fps for smaller file size
- **File Size:** Target < 10MB for GitHub compatibility

### Notes
- Keep cursor movements smooth and deliberate
- Pause briefly at each step to show results
- Ensure text is readable at 800px width
- Include browser address bar to show localhost:8000

Once recorded, replace this file with the actual `demo.gif`.
