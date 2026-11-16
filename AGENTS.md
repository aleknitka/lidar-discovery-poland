# How to work in this repository

This file is for every assistant and every human who works in this project.
It explains how we talk to each other and how we build things.

## 1. How we talk

- Use clear and simple English.
- Do not use short forms. Write every word in full.
- Do not assume the reader knows technical words. If you must use a technical word, explain it in plain language.
- Every answer must be true. Do not guess or make up facts.
- Keep sentences short. One idea per sentence.
- If you are not sure about something, say you are not sure and explain why.

## 2. How we build

- Finish the whole task. Do not stop halfway.
- If you need to make a choice and you are not sure, make the best choice you can. Then clearly write:
  - What you assumed.
  - What other choices you could have made.
  - How we can change it later.
- In nine out of ten cases, your first best choice will be the right one.
- We will correct the one case where it is not.

## 3. How we run things

We use the file called `Makefile` so you only need to remember one command.

- To start the whole project (the data server and the map in the web browser), run:

```
make dev
```

Or, if you do not have `make`:

```
uv run ldp dev
```

This one command sets up the database, starts the server, starts the web page, and opens the browser. Press Control + C to stop everything.

- To check that everything still works after a change, run:

```
make verify
```

This one command runs every check we need:
- It checks the Python code for errors.
- It checks the code style.
- It runs all the tests.
- It checks the web page code.
- It builds the web page for production to make sure it can be built.

You do not need to copy and run many commands. Just run `make verify`.

- To only check style, run `make lint`.
- To only run tests, run `make test`.
- To only build the web page, run `make build`.

If you add a new tool, add it to `make verify` so one command still checks everything.
