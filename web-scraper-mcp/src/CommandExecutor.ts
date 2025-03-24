import { exec } from 'node:child_process';
import { promisify } from 'node:util';
import { openSync, closeSync, appendFileSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import ProcessTracker from './ProcessTracker.js';
import TtyOutputReader from './TtyOutputReader.js';
import { after } from 'node:test';

const execPromise = promisify(exec);
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

class CommandExecutor {
  async executeCommand(command: string): Promise<string> {
    const escapedCommand = this.escapeForAppleScript(command);
    
    try {
      await execPromise(`/usr/bin/osascript -e 'tell application "iTerm2" to tell current session of current window to write text "${escapedCommand}"'`);
      
      // Wait until iterm reports that processing is done
      while (await this.isProcessing()) {
        await sleep(100);
      }
      
      const ttyPath = await this.retrieveTtyPath();
      while (await this.isWaitingForUserInput(ttyPath) === false) {
        await sleep(100);
      }

      // Give a small delay for output to settle
      await sleep(200);
      
      const afterCommandBuffer = await TtyOutputReader.retrieveBuffer()
      return afterCommandBuffer
    } catch (error: unknown) {
      throw new Error(`Failed to execute command: ${(error as Error).message}`);
    }
  }

  async isWaitingForUserInput(ttyPath: string): Promise<boolean> {
    let fd;
    try {
      // Open the TTY file descriptor in non-blocking mode
      fd = openSync(ttyPath, 'r');
      const tracker = new ProcessTracker();
      let belowThresholdTime = 0;
      
      while (true) {
        try {
          const activeProcess = await tracker.getActiveProcess(ttyPath);
          
          if (!activeProcess) return true;

          if (activeProcess.metrics.totalCPUPercent < 1) {
            belowThresholdTime += 350;
            if (belowThresholdTime >= 1000) return true;
          } else {
            belowThresholdTime = 0;
          }

        } catch {
          return true;
        }

        await sleep(350);
      }
    } catch (error: unknown) {
      return true;
    } finally {
      if (fd !== undefined) {
        closeSync(fd);
      }
      return true;
    }
  }

  private escapeForAppleScript(str: string): string {
    // First, escape any backslashes
    str = str.replace(/\\/g, '\\\\');
    
    // Escape double quotes
    str = str.replace(/"/g, '\\"');
    
    // Handle single quotes by breaking out of the quote, escaping the quote, and going back in
    str = str.replace(/'/g, "'\\''");
    
    // Handle special characters
    str = str.replace(/[^\x20-\x7E]/g, (char) => {
      return '\\u' + char.charCodeAt(0).toString(16).padStart(4, '0');
    });
    
    return str;
  }

  private async retrieveTtyPath(): Promise<string> {
    try {
      const { stdout } = await execPromise(`/usr/bin/osascript -e 'tell application "iTerm2" to tell current session of current window to get tty'`);
      return stdout.trim();
    } catch (error: unknown) {
      throw new Error(`Failed to retrieve TTY path: ${(error as Error).message}`);
    }
  }

  private async isProcessing(): Promise<boolean> {
    try {
      const { stdout } = await execPromise(`/usr/bin/osascript -e 'tell application "iTerm2" to tell current session of current window to get is processing'`);
      return stdout.trim() === 'true';
    } catch (error: unknown) {
      throw new Error(`Failed to check processing status: ${(error as Error).message}`);
    }
  }
}

export default CommandExecutor;