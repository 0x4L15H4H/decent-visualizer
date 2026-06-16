.PHONY: dev dev-frontend dev-backend dev-supabase build lint format

dev:
	@make -j3 dev-frontend dev-backend dev-supabase

dev-frontend:
	cd frontend && pnpm dev

dev-backend:
	$(MAKE) -C backend dev

dev-supabase:
	supabase start

lint:
	@$(MAKE) -C backend lint & \
	(cd frontend && pnpm lint) & \
	wait

format:
	@$(MAKE) -C backend format & \
	(cd frontend && pnpm fmt) & \
	wait
