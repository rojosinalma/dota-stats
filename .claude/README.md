# Claude Code Project Configuration

This directory contains persistent context and instructions for Claude Code across sessions.

## Files in this Directory

### `project-context.md`
Contains project-specific information that Claude should know:
- Project overview and tech stack
- Architecture decisions and patterns
- Environment variables and configuration
- Common commands and workflows
- Known issues and current work
- File organization structure

### `coding-standards.md`
Defines coding standards and best practices:
- Style guidelines (NO emojis)
- Naming conventions
- Error handling patterns
- Logging standards
- Git commit format
- Testing requirements
- Security practices
- Performance guidelines
- Code review checklist

### `settings.local.json`
Claude Code permissions configuration:
- Auto-approved bash commands
- Security restrictions
- Tool permissions

## How This Works

When starting a new Claude Code session, you should tell Claude to:
```
Read the .claude/project-context.md file for project context
```

This ensures Claude:
- Remembers your preferences (like no emojis)
- Understands the project architecture
- Follows your coding standards
- Knows about current work and priorities
- Uses the correct commands and patterns

## Updating Context

When you want to add new project-specific instructions:
1. Edit `project-context.md` for project knowledge
2. Edit `coding-standards.md` for coding rules
3. Update TODO.md for current tasks and plans

The next Claude Code session will have access to these updates.

## Tips

- Keep these files updated as the project evolves
- Document architectural decisions as they're made
- Add new environment variables to project-context.md
- Update known issues as bugs are fixed
- Reference these files when onboarding new contributors
