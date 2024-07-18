SERVICE_NAME := CCalendar
SERVICE_DIR  := ../../services/$(SERVICE_NAME)

.PHONY: backend clean distclean

service: backend
	rm -rf $(SERVICE_DIR)/*

# Backend
	cp -r backend $(SERVICE_DIR)
# Frontend
	cp -r frontend $(SERVICE_DIR)
# Generic files
	cp docker-compose.yml deploy.sh $(SERVICE_DIR)
	cp README-FOR-PLAYERS.md $(SERVICE_DIR)/README.md

# Remove all .gitignore files
	find "$(SERVICE_DIR)" -name '.gitignore' -exec rm '{}' \;
# Remove backend source files
	rm -r $(SERVICE_DIR)/backend/cgi
	rm $(SERVICE_DIR)/backend/Makefile
# Remove eventual unneeded files generated on service deploy/startup
	rm -fr $(SERVICE_DIR)/frontend/db
	rm -f $(SERVICE_DIR)/frontend/nginx/*.pem
	rm -f $(SERVICE_DIR)/backend/db/db.sqlite

backend:
	$(MAKE) -C backend

clean:
	$(MAKE) -C backend clean

distclean:
	rm -rf $(SERVICE_DIR)/*
