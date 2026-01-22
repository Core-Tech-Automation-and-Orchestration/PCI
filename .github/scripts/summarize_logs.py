import os
import openai

# Read ECS logs
with open("ecs_task_logs.txt", "r") as f:
    logs = f.read()

# Summarize logs using AI
response = openai.ChatCompletion.create(
    model="gpt-5-mini",
    messages=[
        {"role": "system", "content": "You are a helpful DevOps assistant."},
        {"role": "user", "content": f"Summarize these ECS task logs and highlight errors or warnings:\n{logs}"}
    ]
)

summary = response['choices'][0]['message']['content']

# Save summary to file
with open("log_summary.txt", "w") as f:
    f.write(summary)

# Append summary to GitHub Actions summary
github_summary = os.environ.get("GITHUB_STEP_SUMMARY", "/github/workflow/summary.md")
with open(github_summary, "a") as f:
    f.write("\n## ECS Task Log Summary\n")
    f.write("```\n")
    f.write(summary)
    f.write("\n```\n")

print("AI summary written to GitHub Actions Summary and log_summary.txt")
