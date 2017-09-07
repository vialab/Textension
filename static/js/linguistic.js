var mwd_api_key = "c021ec02-2d18-4e7d-8507-4f940f531e77";

function defineWord($elem) { 
    var text = $elem.data("ocr");
    if(typeof(text)=="undefined") {
        $elem.popover({
            trigger: "manual",
            placement: "top",
            content: function() {
                return "Text unrecognized";
            }
        });
        if(mouse_down) {
            $elem.popover("show");
        }
        return;
    };
    fetch(`http://www.dictionaryapi.com/api/v1/references/collegiate/xml/${text}?key=${mwd_api_key}`)
    .then(function(response) {
        response.text().then(function(data) {
            var xml = $.parseXML(data),
            $xml = $(xml);
            var def_entry = $xml.find("entry").eq(0);
            var pronounciation = def_entry.find("pr").eq(0).text();
            var word_func = def_entry.find("fl").eq(0).text();
            var def_title = text + " (" + pronounciation + ") - " + word_func;
            var dt = def_entry.find("dt");
            var html = "<ol>";
            for(var i = 0; i < dt.length; i++) {
                html += "<li>" + dt.eq(i).text() + "</li>";
                if(i==2) break;
            }
            html += "</ol>";
            if(dt.length == 0) {
                def_title = text;
                html = "No definition";
            }
        
            $elem.popover({
                trigger: "manual",
                placement: "auto",
                title: def_title,
                html: true,
                content: function() {
                    return html;
                }
            });
            if(mouse_down) {
                $elem.popover("show");
            }
        });
    })
    .catch(error => console.error(error));
    
    /* should look like this:
    WORD (pronounciation) - verb
    1 a. Definition
    b. Definition
     */
}

function getDefinition(word) {

}