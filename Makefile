.PHONY: help init web build preview screenshot poster signin badges og qr clean

.DEFAULT_GOAL := help

PORT ?= 1414
PATHS ?= /

help: ## Show this help message
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

init: ## Fetch the Blowfish theme submodule (needed after a fresh clone)
	git submodule update --init --recursive

web: ## Run the dev server on http://127.0.0.1:1414 (override with PORT=)
	hugo server --bind 127.0.0.1 --port $(PORT) --disableFastRender --buildDrafts --buildFuture --navigateToChanged

build: ## Build the production site into public/
	hugo --gc --minify

preview: build ## Build, then serve public/ as static files (what GitHub Pages will send)
	python3 -m http.server $(PORT) --bind 127.0.0.1 --directory public

screenshot: ## Screenshot pages from the dev server (e.g. PATHS="/ /posts/moonhack-2025/")
	bash scripts/dev_screenshot.sh $(PATHS)

poster: ## Render /poster/ to an A4 PDF in .work/data/ (override with OUT=path.pdf)
	bash scripts/make_poster.sh $(OUT)

signin: ## Render /signin/ to an A4 landscape PDF in .work/data/
	bash scripts/make_poster.sh .work/data/moonhack-2026-signin-a4.pdf /signin/

badges: ## Name cards, 8 per A4, from .work/names.txt (override NAMES=, OUT=, BLANK=n extra blanks)
	uv run scripts/make_badges.py $(NAMES) $(if $(OUT),--out $(OUT),) $(if $(BLANK),--blank $(BLANK),)

og: ## Render the 1200x630 social card to static/og-moonhack-2026.png
	bash scripts/make_og.sh $(OUT)

qr: ## Regenerate the poster QR code (override with URL=https://...)
	uv run scripts/make_qr.py $(if $(URL),--url $(URL),)

clean: ## Remove build output and the Hugo resource cache
	rm -rf public resources/_gen .hugo_build.lock
