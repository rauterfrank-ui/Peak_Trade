.PHONY: todo-board todo-board-check

todo-board:
	python3 scripts/build_todo_board_html.py

todo-board-check:
	./scripts/check_todo_board_ci.sh
