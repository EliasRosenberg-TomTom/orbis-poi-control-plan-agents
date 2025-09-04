class AgentConf:

    def load_agent_instructions(filename: str) -> str:
        basePath = "agent_instructions"
        instructions_path = f"{basePath}\\{filename}"
        with open(instructions_path, "r", encoding="utf-8") as file:
            return file.read()