# Start Multi-Agent Session

Initialize a new coordinated multi-agent session with proper folder structure and planning.

## Task Description: $ARGUMENTS

INSTRUCTIONS:

1. Create Session Folder
   First, generate a session ID and create the folder:
   
   SESSION_ID="$(date +%Y-%m-%d_%H-%M)_<task_description>"
   mkdir -p .claude/sessions/$SESSION_ID
      
   Replace <task_description> with a short slug based on the task description provided above.
   
   IMPORTANT: Use this exact SESSION_ID for all subsequent agent invocations. Do not regenerate timestamps during the session.

2. Create Session Plan
   Create a plan.md file in the session folder containing:
   - Objective: One sentence describing what we want to accomplish
   - Subtasks: 3-7 conceptual subtasks needed to complete the objective  
   - Agent Assignments: Which specialized subagents will handle each subtask (use agent-role-number format like senior-ai-engineer-1, documentation-engineer-1, etc.)
   - Validation Criteria: What files must exist and what summaries are required for completion

3. Session Coordination
   You are now the lead agent for this session. When invoking subagents using the Task tool, you MUST:
   
   - Always include SESSION_FOLDER: .claude/sessions/<your_session_folder_name> in the prompt
   - Specify the exact filename format: <agent-role>-<instance>-output.md
   - Include the complete metadata template they should use
   - Pass all necessary context since subagents can't see previous work
   - Validate each subagent's output before proceeding

4. Begin Implementation
   Start executing the plan by invoking the first assigned subagent with proper session context.

Example Task Invocation Pattern:
Task: senior-ai-engineer
Prompt: |
  SESSION_FOLDER: .claude/sessions/$SESSION_ID
  
  FIRST: Read the plan.md file in the session folder to understand the overall objective and your role in the bigger picture.
  
  You are working on: Design authentication system architecture
  
  Context: [Include any relevant background]
  
  Your specific task: Create JWT token validation middleware design
  
  REQUIRED OUTPUT FORMAT:
  - Save as: senior-ai-engineer-1-output.md in the session folder
  - Include metadata block with:
    ---
    session_folder: .claude/sessions/$SESSION_ID
    lead_agent: lead-agent-1
    subagent: senior-ai-engineer-1
    created_at: <UTC_ISO_timestamp>
    ---
  - End with 1-3 sentence summary of what you completed
  
  Return to me: exact filename and summary when done.
Note: Replace $SESSION_ID with the actual session folder name you created in step 1.

Remember: Each subagent works in isolation and cannot see other agents' work unless you explicitly pass that information in your prompts.