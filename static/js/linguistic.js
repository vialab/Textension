/******************************************************************************
 * linguistic.js
 * Functions for linguistic tools to be used on our digital document
 *****************************************************************************/
var mwd_api_key = "c021ec02-2d18-4e7d-8507-4f940f531e77";

// on hover over a word, provide a tool tip that gives it's definition
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
    } else {
        text = text.replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g,"");
    };
    // fetch the data from our dictionary api
    fetch(`https://www.dictionaryapi.com/api/v1/references/collegiate/xml/${text}?key=${mwd_api_key}`)
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
                html = "<ol>";
                def_title = text;
                var suggestions = def_entry.find("suggestion");
                for(var i = 0; i < suggestions.length; i++) {
                    html += "<li>" + suggestions.eq(i).text() + "</li>";
                    if(i==2) break;
                }
                html += "</ol>";
                if(suggestions.length == 0) html = "No definition.";
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
}

// collect all instances of selected word, and provide a map of
// two words before and after each instance
function createContextMap($elem) {
    var og_text = $elem.data("ocr");
    if(typeof(og_text) == "undefined") alert("Word not recognized");

    var $context_map = $("<table/>");
    var text_id = og_text.replace(/[!"#$%&'()*+,.\/:;<=>?@[\\\]^`{|}~]/g, "");
    $context_map.append("<tr><td colspan='2'></td><td class='context-map-title'>" + og_text + "</td><td colspan='2'></td></tr>");
    var text = og_text.replace(/(['"])/g, "\\$1");
    $context_map.attr("id", text_id);
    
    if($("#context-map-container table#" + text_id).length > 0) {
        $("#context-map-container table#" + text_id).remove();
        return;
    }

    var $occurences = $(".img-block:not(.img-patch) img[data-ocr='" + text + "']");
    $occurences.each(function() {
        var curr_id = $(this).attr("id");
        var arr_id = curr_id.split("-");
        var idx_line = parseInt(arr_id[1]);
        var idx_word = parseInt(arr_id[2]);
        var before = [];
        var after = []
        
        if(idx_word > 1) {
            before.push($("#text-" + arr_id[1] + "-" + (idx_word-2).toString()));
        }
        if(idx_word > 0) {
            before.push($("#text-" + arr_id[1] + "-" + (idx_word-1).toString()));
        }
        var last_id = $(".img-block:not(.img-patch)#" + idx_line.toString() + " span img").last().attr("id");
        var arr_last_id = last_id.split("-");
        var idx_last = parseInt(arr_last_id[2]);
        
        if((idx_last-idx_word) >= 2) {
            after.push($("#text-" + arr_id[1] + "-" + (idx_word+2).toString()));
        }
        if((idx_last-idx_word) >= 1) {
            after.push($("#text-" + arr_id[1] + "-" + (idx_word+1).toString()));
        }
        var row_html = "<tr>";
        if(before.length == 2) {
            row_html += "<td class='before'>";
            row_html += before[0][0].outerHTML;
            row_html += "</td>";
            row_html += "<td class='before'>";
            row_html += before[1][0].outerHTML;
            row_html += "</td>";
        } else {
            row_html += "<td colspan='2' class='before'>";
            if(before.length == 1) {
                row_html += before[0][0].outerHTML;
            }
            row_html += "</td>";
        }
        row_html += "<td class='context-map-root'><div class='dot' style='width:" + ($elem.width()+10).toString() + "px;'>" + $elem[0].outerHTML + "</div></td>"
        if(after.length == 2) {
            row_html += "<td class='after'>";
            row_html += after[1][0].outerHTML;
            row_html += "</td>";
            row_html += "<td class='after'>";
            row_html += after[0][0].outerHTML;
            row_html += "</td>";
        } else {
            row_html += "<td colspan='2' class='after'>";
            if(after.length == 1) {
                row_html += after[0][0].outerHTML;
            }
            row_html += "</td>";
        }
        row_html += "</tr>";
        $context_map.append(row_html);
    });
    $context_map.click(function() {
        $(this).remove();
        resizeStage();
    })
    $("#context-map-container").append($context_map);
    resizeStage();
}