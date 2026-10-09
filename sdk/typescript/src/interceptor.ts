import { ChronicleTracer } from "./tracer.js";
import { execSync } from "child_process";

export class SubprocessInterceptor {
  constructor(private tracer: ChronicleTracer) {}

  public execute(command: string, cwd?: string): string {
    this.tracer.recordEvent("subprocess_exec", {
      phase: "start",
      command,
      cwd: cwd || process.cwd(),
    });

    try {
      const output = execSync(command, { cwd, encoding: "utf-8" });
      this.tracer.recordEvent("subprocess_exec", {
        phase: "completed",
        command,
        returncode: 0,
        stdout: output.slice(0, 2000),
      });
      return output;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      this.tracer.recordEvent("subprocess_exec", {
        phase: "completed",
        command,
        returncode: 1,
        stderr: message.slice(0, 2000),
      });
      throw err;
    }
  }
}
