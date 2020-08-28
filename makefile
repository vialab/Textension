.PHONY: tran-extract tran-update tran-compile pretranslation translations

tran-extract :
	pybabel extract -F locales/babel.cfg -k _l -o locales/messages.pot \
	--msgid-bugs-address="vialab.research@gmail.com" \
	--copyright-holder="Vialab" \
	--project="Synonymic Search" \
	--version="1.0" .

tran-update :
	pybabel update -i locales/messages.pot -d locales

tran-compile :
	pybabel compile -d locales

pretranslation : tran-extract tran-update
translations : tran-compile