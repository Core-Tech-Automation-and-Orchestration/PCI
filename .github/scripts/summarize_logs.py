import os
import openai

openai.api_key = os.environ["OPENAI_API_KEY"]

# Read ECS logs
with open("ecs_task_logs.txt", "r") as f:
    logs = f.read()

# Summarize logs using the new OpenAI API
response = openai.chat.completions.create(
    model="gpt-5-mini",
    messages=[
        {"role": "system", "content": "You are a helpful DevOps assistant."},
        {"role": "user", "content": f"Summarize these ECS task logs and highlight errors/warnings:\n{logs}"}
    ]
)

summary = response.choices[0].message.content

# Save summary
with open("log_summary.txt", "w") as f:
    f.write(summary)

# Write to GitHub Actions Summary
github_summary = os.environ.get("GITHUB_STEP_SUMMARY", "/github/workflow/summary.md")
with open(github_summary, "a") as f:
    f.write("\n## ECS Task Log Summary\n```\n")
    f.write(summary)
    f.write("\n```\n")

print("AI summary written to GitHub Actions Summary and log_summary.txt")
