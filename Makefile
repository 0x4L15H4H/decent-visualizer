.PHONY: dev dev-frontend dev-backend build lint format

dev:
	@make -j2 dev-frontend dev-backend

dev-frontend:
	cd frontend && pnpm dev

dev-backend:
	$(MAKE) -C backend dev

lint:
	@$(MAKE) -C backend lint & \
	(cd frontend && pnpm lint) & \
	wait

format:
	@$(MAKE) -C backend format & \
	(cd frontend && pnpm fmt) & \
	wait
