import { exec } from 'node:child_process';
import { promisify } from 'node:util';

const execPromise = promisify(exec);

class SendControlCharacter {
  async send(letter: string): Promise<void> {
    // Validate input
    letter = letter.toUpperCase();
    if (!/^[A-Z]$/.test(letter)) {
      throw new Error('Invalid control character letter');
    }

    // Convert to control code
    const controlCode = letter.charCodeAt(0) - 64;

    // AppleScript to send the control character
    const ascript = `
      tell application "iTerm2"
        tell front window
          tell current session of current tab
            -- Send the control character
            write text (ASCII character ${controlCode})
          end tell
        end tell
      end tell
    `;

    try {
      await execPromise(`osascript -e '${ascript}'`);
    } catch (error: unknown) {
      throw new Error(`Failed to send control character: ${(error as Error).message}`);
    }
  }
}

export default SendControlCharacter;