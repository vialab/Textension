/******************************************************************************
 * interact.js
 * Meat and potatoes of our interactive digital object
 *****************************************************************************/
let canvas, ctx, css_transition, flag = false,
prevX = 0,
currX = 0,
prevY = 0,
currY = 0,
dot_flag = false,
x = "black",
y = 2,
map_height = 150,
haslistener=false,
timeout_id = 0,
mouse_down = false,
expand_width = 0,
vertical_mode = false,
horizontal_mode = false,
resizing = false,
in_transit = 0;

// keep track of mesh and blocks
let mesh = [], block_mesh = [], block_y = [], block_x = [];

// keeps track of active tools
let mode = {
    "draw": false,
    "eraser": false,
    "define": false,
    "grammar": false,
    "context": false,
    "vertical": false,
    "horizontal": false
};

// Toggle a specific active mode
// Sometimes require a series of actions to occur
// or change in functionality based on other active settings
function toggleMode(elem, close_vertical=false, close_horizontal=false, open_vertical=false, open_horizontal=false) {
    let this_mode = $(elem).data("mode");
    if($(elem).is(":checked")) {
        if(close_vertical) {
            closeSpaces(false);
        }
        if(close_horizontal) {
            closeSpaces(true);
        }
        if(open_vertical) {
            openSpaces(false);
        }
        if(open_horizontal) {
            openSpaces(true);
        }
        setActiveMode(this_mode);
    } else {
        let cur_mode = getActiveMode();
        setActiveMode("");
        if(cur_mode == "verticalhorizontal") {
            if(this_mode == "horizontal") {
                $("#vertical-space").click();
            } else {
                $("#horizontal-space").click();                
            }
        }        
    }
}

function getMarginWidth() {
    let margin_width = ($(".stage").width() - $("#vis-container").width()) / 2.0;
    return margin_width;
}

// We have a list of valid modes, and this keeps track of which ones are active
// We use this so that we can have multiple modes active
function setActiveMode(new_mode) {
    for(let type in mode) {
        if(mode.hasOwnProperty(type)) {
            if (new_mode == type) {
                mode[type] = true;
                continue;
            }
            // allow horizontal and vertical to be on together
            if((new_mode=="horizontal" || new_mode=="vertical") && (type=="horizontal" || type=="vertical")) {
                continue;
            }
            if(mode[type]) {
                mode[type] = false;
                disableMode(type);
            }
        }
    }

    if(new_mode != "") {
        togglePointerEvents(true);
    }
}

function togglePointerEvents( on ) {
    if(on) {
        $("input.img-patch-text").css("pointer-events", "none");
    } else {
        $("input.img-patch-text").css("pointer-events", "");
    }
}

// some tools might require more steps to disable, so let's
// throw the disabling into a switch method
function disableMode(type) {
    togglePointerEvents(false);
    switch(type) {
        case "draw":
            $("#draw-tool").prop("checked",false);
            $("canvas#draw-board").addClass("overlay");
            $("#draw-options").hide();
            break;
        case "eraser":
            $("#eraser-tool").prop("checked",false);
            break;
        case "define":
            $("#define-tool").prop("checked",false);
            break;
        case "grammar":
            $("#grammar-tool").prop("checked",false);
            break;
        case "context":
            $("#context-tool").prop("checked",false);
            break;
        case "vertical":
            $("#vertical-space").prop("checked",false);
            break;
        case "horizontal":
            $("#horizontal-space").prop("checked",false);
            break;
        default:
            break;
    }
}

// return the current mode being used
function getActiveMode() {
    let curr_mode = "";
    for(let key in mode) {
        if(mode.hasOwnProperty(key)) {
            if(mode[key]) {
                curr_mode += key;
            }
        }
    }
    return curr_mode;
}

// hide a specific word
function eraseWord($elem) {
    let text_id = $elem.attr("id");
    $("#img-text-id").val(text_id);
    let edit_text = $(".custom-text", $("#"+text_id).parent()).html();
    $("#edit-text").val(edit_text);
    $("#edit-text").height($elem.height());
    $("#edit-text").width($elem.width());
    $("#text-edit").modal("show");
    if($elem.css("opacity") > 0) {
        $("#text-visibility").html("Hide Text");
    } else {
        $("#text-visibility").html("Show Text");
    }
}

// put original pronouns back into the text
function fixPronouns() {
    let $blocks = $(".img-text[data-ocr]").filter(function() {
        return $(this).data("ocr") == "him"
            || $(this).data("ocr") == "her"
            || $(this).data("ocr") == "he"
            || $(this).data("ocr") == "she"
            || $(this).data("ocr") == "his"
            || $(this).data("ocr") == "hers";
    });
    for(let i = 0; i < $blocks.length; i++) {
        let $elem = $($blocks[i]);
        let text_id = $elem.attr("id");
        if($elem.css("opacity") < 1) {
            $elem.css("opacity",1);
            $(".custom-text", $("#"+text_id).parent()).html("");
        }
    }
}

// swap pronouns detected
function replacePronouns(on) {
    let himher = "his/him";
    let heshe = "he";
    let hishers = "his";
    let new_himher = "her";
    let new_heshe = "she";
    let new_hishers = "her(s)";
    if(!on) {
        himher = "her";
        heshe = "she";
        hishers = "hers";
        new_himher = "his/him";
        new_heshe = "he";
        new_hishers = "his";
    }
    let $blocks = $(".img-text[data-ocr]").filter(function() {
        return $(this).data("ocr") == himher
            || $(this).data("ocr") == heshe
            || $(this).data("ocr") == hishers;
    });

    for(let i=0; i<$blocks.length; i++) {
        $("#img-text-id").val($($blocks[i]).attr("id"));
        let old_text = $($blocks[i]).data("ocr");
        let new_text = "";
        switch(old_text) {
            case himher:
                new_text = new_himher;
                break;
            case heshe:
                new_text = new_heshe;
                break;
            case hishers:
                new_text = new_hishers;
                break;
        }
        $("#edit-text").val(new_text);
        saveText();
    }
}

// Set the data elements for all of our detected words
// currently only using this to have OCR text available in the html
function injectMetaData() {
    for(let i=0; i<word_blocks.length; i++) {
        for(let j=0; j<word_blocks[i].length; j++) {
            for(let k=0; k<word_blocks[i][j].length; k++) {
                let text = word_blocks[i][j][k]["text"];
                let idx_block = word_blocks[i][j][k]["idx_block"];
                let word_pos = word_blocks[i][j][k]["word_pos"];
                let text_id = "text-" + i.toString() + "-" + idx_block.toString() + "-" + word_pos.toString();
                $("#" + text_id).attr("data-ocr", text);
            }
        }
    }
}

function saveText() {
    let text = $("#edit-text").val();    
    let text_id = $("#img-text-id").val();
    $(".custom-text", $("#"+text_id).parent()).html(text);
    $("#"+text_id).css("opacity", 0);
    $("#text-visibility").html("Show Text");
}

function replaceAllText() {
    let text = $("#edit-text").val();
    let text_id = $("#img-text-id").val();
    $(".custom-text", $("#"+text_id).parent()).html(text);
    $("#"+text_id).css("opacity", 0);
    $("#text-visibility").html("Show Text");

    let text_ocr = $("#"+text_id).data("ocr");
    if(text_ocr != "") {
        $(".custom-text", $("img[data-ocr='" + text_ocr + "']").parent()).html(text);
        $("img[data-ocr='" + text_ocr + "']").css("opacity",0);
    }
}

function undoAllText() {
    let text_id = $("#img-text-id").val();
    let $elem = $("#" + text_id);
    $elem.css("opacity",1);
    $("#text-visibility").html("Hide Text");     
    $(".custom-text", $("#"+text_id).parent()).html("");   
    $("#edit-text").val("");
    let text_ocr = $("#"+text_id).data("ocr");
    if(text_ocr != "") {
        $(".custom-text", $("img[data-ocr='" + text_ocr + "']").parent()).html("");
        $("img[data-ocr='" + text_ocr + "']").css("opacity",1);
    }
}

function toggleTextVisibility() {
    let text_id = $("#img-text-id").val();
    let $elem = $("#" + text_id);
    if($elem.css("opacity") > 0) {
        $elem.css("opacity",0);
        $("#text-visibility").html("Show Text");        
    } else {
        $elem.css("opacity",1);
        $("#text-visibility").html("Hide Text");     
        $(".custom-text", $("#"+text_id).parent()).html("");   
        $("#edit-text").val("");
    }
}

function toggleSingleSpace($elem, is_horizontal) {
    in_transit++;
    if(is_horizontal) {
        let $parent = $elem.parent();
        if($parent.hasClass("squeeze")) {
            $parent.removeClass("squeeze");
            space_width = $parent.data("img-width");
            stock_width = $parent.width();
            $parent.transition({width:space_width}, detectResizeStage);
            block_id = $parent.parent().attr("id");
            justifyDocument(block_id, (space_width-stock_width));
        } else {
            // disabled - requires implementation of reverse justification
            // $parent.addClass("squeeze");
            // $parent.width(0);
        }
    } else {
        if($elem.hasClass("squeeze")) {
            $elem.removeClass("squeeze");
            space_height = $elem.data("img-height");
            if($("#location").is(":checked")) {
                if($elem.data("map-height") > 0) {
                    space_height = $elem.data("map-height");
                }
            }
            $elem.transition({height:space_height}, detectResizeStage);
        } else {
            $elem.transition({height:0}, detectResizeStage);
            $elem.addClass("squeeze");
        }
    }
}

// When we open a space, distribute the same amount of space across all lines
// in order to keep the edges of our document in line
function justifyDocument(idx, space_width) {
    $(".img-block").each(function(x){
        if(!$(this).hasClass("img-patch") && $(this).attr("id")==idx) {
            return;
        }
        let $spaces = $("span.text-space.squeeze", $(this));
        if($spaces.length > 0) {
            let added_width = 0;
            let iter_width = space_width;
            while(added_width < space_width) {
                let target_width = Math.floor(space_width/$spaces.length);
                let extra_width = space_width - (target_width*$spaces.length);
                in_transit += $spaces.length;
                $spaces.each(function(i) {
                    let add_width = target_width + $(this).width();
                    let full_width = $(this).data("img-width");
                    if(add_width >= full_width) {
                        $(this).removeClass("squeeze");
                        add_width = full_width;
                    } else {
                        // sneak some of the extra width as we go
                        if(full_width>add_width && extra_width > 0) {
                            let extra_diff = extra_width-(full_width-add_width);
                            if(extra_diff <= 0) {
                                add_width += extra_width;
                                extra_width = 0;
                            } else {
                                add_width += extra_width-extra_diff;
                                extra_width = extra_diff;
                            }
                            if(extra_diff >= 0) {
                                $(this).removeClass("squeeze");
                                add_width = full_width;
                            }
                        }
                    }
                    $(this).transition({width:add_width}, detectResizeStage);
                    added_width += add_width;
                });
                $spaces = $("span.text-space.squeeze", $(this));
            }
        }
    });        
}

// based on whatever mode is selected, open the required spaces
// if no mode is selected, open everything
function openActiveSpaces() {
    let active_mode = getActiveMode();
    if(active_mode == "horizontal") {
        openSpaces(true);        
    } else if(active_mode == "vertical") {
        openSpaces(false);        
    } else {
        openSpaces(false);
        openSpaces(true);
    }
}

// based on whatever mode is selected, close the required spaces
// if no mode is selected, close everything
function closeActiveSpaces() {
    let active_mode = getActiveMode();
    if(active_mode == "horizontal") {
        closeSpaces(true);
    } else if(active_mode == "vertical") {
        closeSpaces(false);
    } else {
        $("#vertical-space").prop("checked", false);
        $("#horizontal-space").prop("checked", false);
        setActiveMode("");
        resizing = true;
        closeSpaces(false);
        resizing = false;
        closeSpaces(true);
    }
}

function toggleSpace( is_horizontal ) {
    if(getActiveMode() != "") setActiveMode("");
    if(is_horizontal) {
        if($(".text-space:not(.squeeze)").length > 0) {
            closeSpaces(true);
        } else {
            openSpaces(true);
        }
    } else {
        if($(".img-patch:not(.squeeze)").length > 0) {
            closeSpaces(false);
        } else {
            openSpaces(false);
        }
    }        
}

function openSpaces( is_horizontal ) {
    let deferrals = [];
    $(".vis-container").each(function(i, $e) {
        let block_num = $(this).data("block");
        if(is_horizontal) {
            $(".text-space",$e).removeClass("squeeze");
            $(".text-space",$e).each(function() {
                in_transit++;
                space_width = $(this).data("img-width");
                // $(this).width(space_width);
                deferrals.push($(this).transition({width:space_width}).promise());
            });
        } else {
            $(".img-patch",$e).removeClass("squeeze");
            $(".img-patch",$e).each(function() {
                in_transit++;
                space_height = $(this).data("img-height");
                if($("#location",$e).is(":checked")) {
                    if($(this).data("map-height") > 0) {
                        space_height = $(this).data("map-height");
                    }
                }
                deferrals.push($(this).transition({height:space_height}).promise());
            });
        }
    });
    $.when(...deferrals).done(function() {
        resetBlockMesh();
        for(let i=0; i < block_mesh.length; i++) resizeBlockMesh(i);
        mapBlockMesh();
    })
}

function closeSpaces( is_horizontal ) {
    let deferrals = [];
    $(".vis-container").each(function(i, $e) {
        block_num = $(this).data("block");
        space_size = 0;
        if(is_horizontal) {
            in_transit += $(".text-space",$e).length;
            deferrals.push($(".text-space",$e).transition({width:0}).promise());
            $(".text-space",$e).addClass("squeeze");
        } else {
            in_transit += $(".img-patch",$e).length;
            deferrals.push($(".img-patch",$e).transition({height:0}).promise());
            $(".img-patch",$e).addClass("squeeze"); 
        }
    });
    $.when(...deferrals).done(function() {
        resetBlockMesh();
        for(let i=0; i < block_mesh.length; i++) resizeBlockMesh(i);
        mapBlockMesh();
    })
}


// hide or show page selection bar on the bottom
function togglePageOptions() {
    if($("#page-options:not(.squeeze)").length > 0) {
        $("#page-options").css("bottom", "-135px");
        $("#page-options").addClass("squeeze");
        $("#page-options-toggle").html("▲");
    } else {
        $("#page-options").css("bottom", "0");
        $("#page-options").removeClass("squeeze");
        $("#page-options-toggle").html("▼");
    }
}

// Place the appropriate symbols indicating a words uniqueness level
function setUniqueness(dateval) {
    let idx_date = dateval - 1800;
    let usage_list = [];
    for(let i=0; i<ngram_plot.length; i++) {
        usage_list.push(ngram_plot[i]["usage"][idx_date]);
    }
    usage_list = argsort(usage_list, true);

    for(let rank=0; rank<usage_list.length; rank++) {
        let i = usage_list.sort_indices[rank];
        let norm_rank = rank;
        if (rank > 0) {
            let last_rank = rank-1;
            let last_idx = usage_list.sort_indices[last_rank];
            while(ngram_plot[i]["usage"][idx_date] == ngram_plot[last_idx]["usage"][idx_date] && last_rank > 0) {
                last_rank--;
                last_idx = usage_list.sort_indices[last_rank];
            }
            norm_rank = last_rank;
        }
        let idx_block = ngram_plot[i]["idx_block"];
        let idx_word = ngram_plot[i]["word_pos"];
        let id = "unique-" + idx_block.toString() + "-" + idx_word.toString();
        let patch_height = $("#"+id).closest("div.img-patch").data("img-height");
        let img_url = "uniqueness_0.png";
        let image_rank = (norm_rank/usage_list.length);

        if(image_rank >= 0.8) {
            img_url = "uniqueness_4.png";
        } else if(image_rank >= 0.6) {
            img_url = "uniqueness_3.png";
        } else if(image_rank >= 0.4) {
            img_url = "uniqueness_2.png";
        } else if(image_rank >= 0.2) {
            img_url = "uniqueness_1.png";
        } else {
            img_url = "uniqueness_0.png";
        }

        $("#"+id).css("background", "url('./static/css/" + img_url + "')");
        $("#"+id).css("background-size", "100% 100%");
        if(patch_height > 15) {
            patch_height = 15;
        }
        $("#"+id).height(patch_height);
    }
}

// Place the appropriate graphs as an overlay in the correct positions
// This includes:
//  - OCR confidence highlighting
//  - NGram Plots
//  - Uniqueness Glyphs
function drawOverlays() {
    // iterate through each block
    for(let i=0; i<word_blocks.length; i++) {
        // iterate through each line
        for(let j=0; j<word_blocks[i].length; j++) {
            // within each line, iterate each word that we detected
            for(let k=0; k<word_blocks[i][j].length; k++) {
                // generate highlight blocks or OCR confidence
                let opacity = (word_blocks[i][j][k]["confidence"]/100.0);
                opacity = (1.00-Math.max((Math.round(opacity * 5) / 5), 0.1)).toFixed(2) * 0.9;
                let idx_block = word_blocks[i][j][k]["idx_block"];
                let idx_word = word_blocks[i][j][k]["word_pos"];
                let text_id = "#text-" + i.toString() + "-" + idx_block.toString() + "-" + idx_word.toString();
                let patch_id = "#patch-" + i.toString() + "-" + idx_block.toString() + "-" + idx_word.toString();
                let $conf = $("<div/>", {"class":"text-confidence"});
                $conf.css("opacity", opacity);
                $conf.width(word_blocks[i][j][k]["width"]);
                $conf.height(word_blocks[i][j][k]["height"]);
                $conf.css("top", word_blocks[i][j][k]["y"] + "px");
                if(idx_word == 0) {
                    $conf.css("left", word_blocks[i][j][k]["x"] + "px");                
                }
                $(text_id).parent().append($conf);
                // place our NGRAM plots (raw base64 strings) and place them in as img elements
                for(let y=0; y<ngram_plot.length; y++) {
                    if(ngram_plot[y]["idx_block"] == idx_block && ngram_plot[y]["word_pos"]==idx_word) {
                        let $img = $("<img/>",{"class":"ngram-usage"});
                        $img.attr("src", "data:image/png;base64,"+ngram_plot[y]["ngram"]);
                        if(idx_word==0) {
                            $img.css("left",word_blocks[i][j][k]["x"]+"px");
                        }
                        $(patch_id).parent().append($img);
                        break;
                    }
                }

                // place the uniqueness glyph placeholders
                let $uniqueness = $("<span/>", {"id":"unique-" 
                    + idx_block + "-" + idx_word, "class":"uniqueness-bar"});
                $uniqueness.css({"height":"0px", "width":"20px"});
                if(idx_word==0) {
                    $uniqueness.css("left",word_blocks[i][j][k]["x"]+"px");
                }
                $(patch_id).parent().append($uniqueness);
            }
        }
    }
}

// insert base64 strings as imgs into the DOM and also highlight the locations
function drawLocations() {
    for(let i=0; i<word_blocks.length; i++) {
        for(let j=0; j<word_blocks[i].length; j++) {
            if(word_blocks[i][j]["label"] == "GPE") {
                // draw the overlay color box
                let idx_block = word_blocks[i][j]["idx_block"];
                let idx_word = word_blocks[i][j]["word_pos"];
                let text_id = "#text-" + idx_block.toString() + "-" + idx_word.toString();
                let $loc = $("<div/>", {"class":"entity-location"});
                $loc.width(word_blocks[i][j]["width"]);
                $loc.height(word_blocks[i][j]["height"]);
                $loc.css("top", word_blocks[i][j]["y"] + "px");
                if(idx_word == 0) {
                    $loc.css("left", word_blocks[i][j]["x"] + "px");                
                }
                $(text_id).parent().append($loc);
                // draw the map
                let $img = new Image();
                $img.src = "data:image/png;base64,"+word_blocks[i][j]["map"];
                $($img).css("top", $(text_id).parent().parent().position().top + "px");
                $($img).data("word-id",text_id);
                $("#entity-map-container").append($img);
            }
        }
    }
}

// Initialize the usable canvas for drawing
function init() {
    canvas = document.getElementById('draw-board');
    ctx = canvas.getContext("2d");
    canvas.width=$(".vis").width();
    canvas.height=$(".vis").height();
    $("#draw-board").width(canvas.width);
    $("#draw-board").height(canvas.height);
    w = canvas.width;
    h = canvas.height;
    
    // remove the mouse event listeners if they already exist
    if(haslistener) {
        canvas.removeEventListener("mousemove");
        canvas.removeEventListener("mousedown");
        canvas.removeEventListener("mouseup");
        canvas.removeEventListener("mouseout");
    }

    canvas.addEventListener("mousemove", function (e) {
        findxy('move', e)
    }, false);
    canvas.addEventListener("mousedown", function (e) {
        findxy('down', e)
    }, false);
    canvas.addEventListener("mouseup", function (e) {
        findxy('up', e)
    }, false);
    canvas.addEventListener("mouseout", function (e) {
        findxy('out', e)
    }, false);

    haslistener = true;
}

// set inline styles based on the color element selected
function textColor(obj) {
    $("#text-color-select").css("background-color", obj.id);
    $(".img-patch-text").css("color", obj.id);
    $(".custom-text").css("color", obj.id);
}

// draw functionality for mouse down events while draw mode is activated
function draw() {
    ctx.beginPath();
    ctx.moveTo(prevX, prevY);
    ctx.lineTo(currX, currY);
    ctx.strokeStyle = x;
    ctx.lineWidth = y;
    ctx.stroke();
    ctx.closePath();
}

// erase button click event
function erase() {
    let m = confirm("Are you sure you would like to clear?");
    if (m) {
        ctx.clearRect(0, 0, w, h);
        // document.getElementById("canvasimg").style.display = "none";
    }
}

// download the current html canvas as an image
function print() {
    html2canvas($(".vis"), {
        onrendered: function (canvas) {
            // Convert and download as image 
            Canvas2Image.saveAsPNG(canvas);
        }
    });
}

// track the mouse and draw when the mouse is pressed and moving
function findxy(res, e) {
    rect = canvas.getBoundingClientRect();
    if (res == 'down') {
        prevX = currX;
        prevY = currY;
        currX = e.clientX - rect.left;
        currY = e.clientY - rect.top;

        flag = true;
        dot_flag = true;
        if (dot_flag) {
            ctx.beginPath();
            ctx.fillStyle = x;
            ctx.fillRect(currX, currY, 2, 2);
            ctx.closePath();
            dot_flag = false;
        }
    }
    if (res == 'up' || res == "out") {
        flag = false;
    }
    if (res == 'move') {
        if (flag) {
            prevX = currX;
            prevY = currY;
            currX = e.clientX - rect.left;
            currY = e.clientY - rect.top;
            draw();
        }
    }
}

// return a list of indices that would sort an array
function argsort(to_sort, desc=false) {
    for (let i = 0; i < to_sort.length; i++) {
      to_sort[i] = [to_sort[i], i];
    }
    to_sort.sort(function(left, right) {
        if(desc) {
            return left[0] > right[0] ? -1 : 1;
        } else {
            return left[0] < right[0] ? -1 : 1;
        }
    });
    to_sort.sort_indices = [];
    for (let j = 0; j < to_sort.length; j++) {
      to_sort.sort_indices.push(to_sort[j][1]);
      to_sort[j] = to_sort[j][0];
    }
    return to_sort;
}
