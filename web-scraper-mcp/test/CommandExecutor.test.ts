import CommandExecutor from '../src/CommandExecutor.js';
import TtyOutputReader from '../src/TtyOutputReader.js';

async function testExecuteCommand() {
  const executor = new CommandExecutor();
  // Combine all arguments after the script name into a single command
  const command = process.argv.slice(2).join(' ') || 'date';
  
  try {
    const beforeCommandBuffer = await TtyOutputReader.retrieveBuffer();
    const beforeCommandBufferLines = beforeCommandBuffer.split("\n").length;

    await executor.executeCommand(command);

    const afterCommandBuffer = await TtyOutputReader.retrieveBuffer();
    const afterCommandBufferLines = afterCommandBuffer.split("\n").length;
    const outputLines = afterCommandBufferLines - beforeCommandBufferLines
    
    const buffer = await TtyOutputReader.call(outputLines)
    console.log(buffer);

    console.log(`Lines: ${outputLines}`);
  } catch (error) {
    console.error('Error executing command:', (error as Error).message);
  }

  
}

testExecuteCommand();