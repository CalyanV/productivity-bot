# User Guide

Complete guide to using the Self-Auditing Productivity System.

## Table of Contents

- [Getting Started](#getting-started)
- [Daily Workflow](#daily-workflow)
- [Task Management](#task-management)
- [Calendar Integration](#calendar-integration)
- [People & CRM](#people--crm)
- [Check-ins](#check-ins)
- [Settings & Customization](#settings--customization)
- [Advanced Features](#advanced-features)
- [Tips & Best Practices](#tips--best-practices)

## Getting Started

### First Interaction

1. **Start the bot**: Send `/start` to your bot
2. **You'll receive**: Welcome message with quick overview
3. **Try basic commands**: `/help` to see all available commands

### Your First Task

Just send a message describing what you need to do:

```
"Finish the project proposal by Friday"
```

The bot will:
- ✅ Create a task
- 📅 Set Friday as due date
- 🤖 Estimate time needed
- 📝 Save to database and Obsidian

## Daily Workflow

### Morning (Default: 4:30 AM)

**You'll receive a morning check-in prompt:**

```
🌅 Good morning! Time for your daily check-in.

Let's make today count! 💫

**Energy Level** (1-10):
How are you feeling physically and mentally?

**Mood**:
In a word or two, how would you describe your mood?

**Daily Habits**:
✅ Exercise
✅ Meditation
✅ Healthy breakfast

**Today's Top 3 Priorities**:
1.
2.
3.
```

**How to respond:**

```
Energy: 8
Mood: Focused and ready
Habits: Exercise ✓, Meditation ✓, Breakfast ✓
Priorities:
1. Finish proposal
2. Call with John
3. Review team submissions
```

The bot creates a daily log in your Obsidian vault with this information.

### During the Day (Every 2 hours, 9 AM - 5 PM)

**You'll receive periodic check-ins:**

```
⏰ Quick check-in!

**What are you working on right now?**
```

**Quick response:**
```
"Working on the marketing deck"
```

This helps you:
- Stay aware of what you're actually doing
- Compare planned vs. actual work
- Catch yourself when distracted

### Evening (Default: 8:00 PM)

**You'll receive an evening review:**

```
🌙 Time for your evening review!

**Energy Level** (1-10):
**Mood**:
**What did you accomplish today?**
**What's still pending?**
**One thing you learned today?**
**Tomorrow's Top Priority**:
```

**How to respond:**

```
Energy: 6
Mood: Satisfied
Accomplished:
- ✅ Finished proposal
- ✅ Called John
- ✅ Reviewed 8/10 submissions

Still pending:
- Review last 2 submissions
- Schedule follow-up meeting

Learned: Time-blocking in morning is more effective than afternoon

Tomorrow: Send proposal to client
```

## Task Management

### Adding Tasks

#### Natural Language

Just send a message:

```
"Call Sarah about the budget next week"
→ Creates task with estimated due date

"Meeting prep for Monday 2pm, need 30 minutes"
→ Creates task with specific due date and time estimate

"Buy groceries after work today"
→ Creates task for today with context
```

#### Using `/add` command

```
/add Review code before standup tomorrow
/add Write blog post about productivity, high priority
/add Email team about deadline @work @urgent
```

### Viewing Tasks

```
/tasks              # All active tasks
/tasks today        # Today's tasks
/tasks week         # This week's tasks
/tasks overdue      # Overdue tasks
```

**Example output:**

```
You have 5 tasks (showing 5):

📋 Review code before standup
    Due: Tomorrow
    Priority: Medium
    Estimated: 30 minutes

📋 Email team about deadline
    Due: Today
    Priority: High
    Tags: work, urgent
```

### Task Properties

The bot automatically extracts:

- **Title**: Main task description
- **Due date**: "tomorrow", "Friday", "next week", "Jan 31"
- **Time estimate**: Based on task complexity
- **Priority**: "high", "medium", "low"
- **People**: Mentions like "with John" or "to Sarah"
- **Tags**: Words starting with @ or #
- **Project**: If mentioned (e.g., "for website redesign")

## Calendar Integration

### Scheduling Tasks

#### Automatic Scheduling

```
/schedule task-123
```

The bot will:
1. 🔍 Find free time slots in your calendar
2. ⏰ Suggest the best time based on task duration
3. 📅 Create calendar event
4. 🔗 Link event to task in Obsidian

**Example response:**

```
✅ Task scheduled!

📋 Review code before standup
📅 Tuesday, January 31
⏰ 09:30 AM
🔗 View in Calendar

Other available slots:
1. Tue Jan 31 at 02:00 PM
2. Wed Feb 01 at 10:00 AM
```

#### Finding Time Slots

```
/suggest 60           # Find 60-minute slots
/suggest 120          # Find 2-hour slots
```

**Example response:**

```
📅 Available 60-minute slots:

1. Tuesday, January 31 at 09:00 AM
2. Tuesday, January 31 at 02:30 PM
3. Wednesday, February 01 at 10:00 AM
4. Wednesday, February 01 at 03:00 PM
5. Thursday, February 02 at 11:00 AM
```

#### Viewing Calendar

```
/calendar
```

Shows upcoming events from your Google Calendar.

### Bidirectional Sync

Changes in Google Calendar automatically update tasks:

- ✅ Mark event as complete → Task marked complete
- 🗑️ Delete event → Task unscheduled
- ⏰ Reschedule event → Task due date updated

## People & CRM

### Adding People

```
/person John Doe
```

**If not found, bot creates new contact:**

```
✅ Added John Doe to your network!

ID: person-abc123

Update details with /person person-abc123
```

### Viewing All People

```
/people
```

**Example output:**

```
📇 Your Network:

• John Doe - CEO @ Acme Corp
• Sarah Smith - Designer @ Creative Studio
• Mike Johnson - Developer

💡 Use /person <name> to view details
```

### Viewing Person Details

```
/person person-abc123
```

**Example output:**

```
**John Doe**

**Role**: CEO
**Company**: Acme Corp
**Email**: john@acme.com
**Phone**: +1-555-0123

**Last Contact**: January 15, 2026

**ID**: person-abc123
```

### Updating Last Contact

```
/contact person-abc123
```

**Response:**

```
✅ Updated last contact for John Doe
Date: January 31, 2026
```

### Automatic Contact Tracking

When you mention someone in a task:

```
"Call John about the proposal"
```

The bot:
1. Links task to John's contact
2. Updates conversation history
3. Tracks this interaction

## Check-ins

### Morning Check-in

**Customizing the prompt:**

Use `/settings` to adjust:
- Check-in time
- Habits to track
- Number of priorities

**Best practices:**
- ⚡ Keep energy honest (helps spot patterns)
- 🎯 Limit to 3 priorities (forces focus)
- ✅ Track same habits daily (builds consistency)

### Periodic Check-ins

**Purpose:**
- Catch yourself when distracted
- Build awareness of time usage
- Compare planned vs. actual work

**Customizing:**
```
/settings periodic_checkin_interval_hours 3  # Every 3 hours
/settings periodic_checkin_start_hour 8       # Start at 8 AM
/settings periodic_checkin_end_hour 18        # End at 6 PM
```

**Disable if distracting:**
```
/settings periodic_checkin_enabled false
```

### Evening Review

**Why it matters:**
- Celebrate wins (even small ones)
- Acknowledge what's pending
- Extract learnings
- Prime tomorrow's focus

**Best practices:**
- 📊 Be specific about accomplishments
- 🧠 Extract one concrete learning
- 🎯 Choose ONE top priority for tomorrow
- 💤 Use this as transition to evening

## Settings & Customization

### View Current Settings

```
/settings
```

**Example output:**

```
⚙️ Your Settings

🌍 Timezone: America/New_York

⏰ Check-in Times:
• Morning: 04:30
• Evening: 20:00
• Periodic: Enabled
  Every 2 hours (9:00 - 17:00)

🔔 Notifications:
• Priority: default
• Tags: productivity, tasks

📅 Work Schedule:
• Hours: 9:00 - 17:00
• Exclude weekends: Yes
```

### Update Settings

```
/settings timezone America/Los_Angeles
/settings morning_checkin_time 05:00
/settings work_hours_start 8
/settings work_hours_end 18
/settings exclude_weekends false
```

### Reset to Defaults

```
/settings reset
```

## Advanced Features

### Voice Messages

Send a voice message instead of typing:

1. 🎤 Record voice message in Telegram
2. 🤖 Bot transcribes using Whisper
3. ✅ Processes as task/note

**Great for:**
- Capturing ideas while driving
- Quick brain dumps
- When typing is inconvenient

### Natural Language Understanding

The bot understands context:

```
"Follow up on the proposal we sent last week"
→ Creates task, links to relevant context

"Schedule 1:1 with Sarah for next week, 30 minutes"
→ Creates task AND calendar event

"Remind me to check in with the team after launch"
→ Creates task with relative due date
```

### Multi-turn Conversations

The bot maintains context:

```
You: "Create a task for the client meeting"
Bot: "Got it! When should this be scheduled?"
You: "Next Tuesday at 2pm"
Bot: "Perfect! I've scheduled the client meeting for Tuesday, Feb 1 at 2:00 PM"
```

### Project Tracking

Mention projects in tasks:

```
"Review design mockups for website redesign project"
```

Bot automatically:
- Creates/links to project
- Groups related tasks
- Tracks project progress

### Git Sync

If enabled, your Obsidian vault syncs to Git:

- ✅ Automatic commits when you add/update tasks
- 🔄 Pull changes from other devices
- 🤝 Conflict resolution for multi-device usage
- 📜 Full history of changes

## Tips & Best Practices

### Task Capture

✅ **DO:**
- Capture immediately when you think of it
- Use natural language
- Include context and why
- Set realistic deadlines

❌ **DON'T:**
- Wait to "organize later"
- Make tasks too vague
- Skip time estimates
- Create duplicate tasks

### Calendar Blocking

✅ **DO:**
- Block time for deep work
- Include buffer time
- Respect your calendar
- Review schedule each morning

❌ **DON'T:**
- Overbook your day
- Schedule back-to-back meetings
- Ignore your energy levels
- Forget breaks

### Daily Check-ins

✅ **DO:**
- Be honest about energy/mood
- Review previous day's check-in
- Celebrate small wins
- Extract concrete learnings

❌ **DON'T:**
- Rush through check-ins
- Judge yourself for low productivity
- Skip reflection
- Set unrealistic priorities

### People Management

✅ **DO:**
- Add people as you interact
- Log contact after conversations
- Include context in notes
- Set follow-up reminders

❌ **DON'T:**
- Wait to batch-add people
- Forget to log interactions
- Leave fields empty
- Lose touch with your network

### Productivity Patterns

Track these over time:

- 📊 **Energy patterns**: When are you most focused?
- ⏰ **Time estimates**: Are you getting better?
- ✅ **Completion rates**: What's your success rate?
- 🎯 **Priority alignment**: Do you work on what matters?

## Keyboard Shortcuts

In Telegram:

- `Ctrl/Cmd + K` - Search commands
- `Up Arrow` - Edit last message
- `@botusername` - Mention in groups
- `/` - See command list

## Common Workflows

### Weekly Review

```
1. /tasks week              # Review week's tasks
2. Check daily logs         # Review each day's check-ins
3. /people                  # Review relationships
4. /calendar               # Preview next week
5. Plan next week's priorities
```

### Before Important Meeting

```
1. /person <name>          # Review person's details
2. Check previous tasks    # See conversation history
3. /schedule <prep-task>   # Block prep time
4. Add follow-up reminders
```

### End of Day Shutdown

```
1. Evening check-in        # Reflect on the day
2. /tasks tomorrow         # Review tomorrow's tasks
3. Brain dump pending items
4. Set tomorrow's #1 priority
5. Close laptop
```

### Managing Overwhelm

```
1. Brain dump everything   # Capture all open loops
2. /tasks                  # See full list
3. Prioritize ruthlessly   # Pick top 3
4. Defer or delete rest    # Be honest
5. Focus on one thing      # Start with smallest
```

## Getting Help

- `/help` - List all commands
- Check logs for errors
- See [SETUP.md](SETUP.md) for troubleshooting
- GitHub Issues for bugs
- GitHub Discussions for questions

## What's Next?

1. **Build the habit**: Use daily for 30 days
2. **Track patterns**: Review weekly
3. **Adjust settings**: Fine-tune to your rhythm
4. **Extend**: Add more integrations
5. **Share**: Help others get organized
