# net-auto.nl - NLNAM Website

This repository contains the source files for [net-auto.nl](https://net-auto.nl), the website of the Netherlands Network Automation Meetup (NLNAM).

## Serving the site locally

This depends on `uv` and some packages from `brew`.  If you are working on a Mac. Just run `task init` to install the dependencies.

To serve the site locally, run:

```bash
    task serve
```

## Create a new event
To create a new event, run:

```bash
    task post
```

This will prompt you for the event details and create a new markdown file and opens it in vscode. It may need some minor adjustments before publishing.

## Create reminders
To create reminders for upcoming events, run:

```bash
    task create_reminders
```

It will dynamically create reminder text files for LinkedIn posts for RFP and event announcements in the `reminders` folder, based on the next upcoming event. You can then copy-paste the content to LinkedIn when needed.

## Contributing
Contributions are welcome! Please feel free to open issues or submit pull requests.
