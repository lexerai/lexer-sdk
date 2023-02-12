# Lexer Configuration Management

There are many ways to configure Lexer - Python decorator, API calls, user defined Lexer config files etc.

Here's how we would process the flags/values in order of precedence:

1. **Lexer APIs**

* Explicitly provided arguments to the `@Lexer` decorator and Lexer APIs like `benchmark(torch_model, input, ...)` and `export(torch_model, input, ...)`.

2. **Lexer user config file (`.lexer_config.toml`)**

* This is a configuration file that contains config values the user would like to overwrite over
the provided defaults or undefined in Lexer APIs (step 1).
* The Lexer user config file must be named `.lexer_config.toml` and the `LEXER_CONFIG_PATH` environment
variable be defined if not in the `$HOME` directory.

3. **Lexer's default config file**

* We will use the Lexer variables as defaults.
