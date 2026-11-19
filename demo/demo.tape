# Record with:  vhs demo/demo.tape   (from the repo root)
Output demo/demo.gif

Require uv
Require bat

Set Shell "bash"
Set FontSize 15
Set Width 1400
Set Height 950
Set Padding 24
Set Theme "Catppuccin Mocha"
Set TypingSpeed 45ms

Hide
Type "uv sync -q && cd demo && rm -f demo.png && export PS1='\[\e[1;35m\]❯\[\e[0m\] ' && clear"
Enter
Show

Type "# plotnine-ggtext: markdown & HTML text for plotnine"
Sleep 600ms
Enter
Type "bat --style=numbers --paging=never demo.py"
Enter
Sleep 7s

Type "uv run python demo.py"
Enter
Sleep 3s

Type "clear && cd .. && uv run pytest -q"
Enter
Sleep 7s
