var canvas, ctx, css_transition, flag = false,
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

var mode = {
    "draw": false,
    "eraser": false,
    "define": false,
    "grammar": false,
    "context": false,
    "vertical": false,
    "horizontal": false
};

$(document).ready(function() {
    var width = "-" + ($(".tool-box").width()+5).toString() + "px";
    $(".tool-box").css({"transform":"translateX(" + width + ")"});
    resizeStage();

    $(".img-block:not(.img-patch)").on("click", function() {
        if (getActiveMode() != "vertical") return;
        var id = parseInt($(this).attr("id"));
        if(id == 0) {
            return;
        }
        toggleSingleSpace($("#"+id.toString()+".img-patch"), false)
    });
    injectMetaData();

    drawConfidence();
    $(".text-confidence").hide();
    $("#confidence").on("click", function() {
        if($(this).is(":checked")) {
            $(".text-confidence").show();            
        } else {
            $(".text-confidence").hide();            
        }
    });

    drawUniqueness();
    $("#uniqueness-range").hide();
    $("#uniqueness").on("click", function() {
        if($(this).is(":checked")) {
            openSpaces(false);
            setUniqueness( $("#uniqueness-range input").val() );
            $("#uniqueness-range").show();
            $(".switch").css("height", "15%");
        } else {
            $("div.uniqueness-chart span").height(0);
            $("#uniqueness-range").hide();
            $(".switch").css("height", "16%");
        }
    });

    var rangeSlider = function(){
        var slider = $('.range-slider'),
            range = $('.range-slider__range'),
            value = $('.range-slider__value');
        slider.each(function(){
        
            value.each(function(){
            var value = $(this).prev().attr('value');
            $(this).html(value);
            });
        
            range.on('input', function(){
            $(this).next(value).html(this.value);
            });
        });
    };
      
    rangeSlider();

    drawNGramUsage();
    $("canvas.ngram-usage").hide();
    $("#ngram").on("click", function() {
        if($(this).is(":checked")) {
            openSpaces(false);            
            $("canvas.ngram-usage").show();
        } else {
            $("canvas.ngram-usage").hide();            
        }
    });

    drawLocations();    
    $(".entity-location").hide();
    $("#entity-map-container").hide();
    $("#location").on("click", function() {
        if($(this).is(":checked")) {
            $(".entity-location").show();
            $("#entity-map-container").show();
        } else {
            $(".entity-location").hide();
            $("#entity-map-container").hide();
        }
        resizeStage();
    });

    // ACTIVE TOOLS
    $("#draw-tool").on("click", function() {
        if($(this).is(":checked")) {
            setActiveMode("draw");
            $("canvas#draw-board").removeClass("overlay");
            $("#draw-options").show();
            if(!haslistener) init();
        } else {
            setActiveMode("");
            $("#draw-options").hide();            
        }
    });

    $(".img-block:not(.img-patch) img").on("click", function() {
        switch(getActiveMode()) {
            case "eraser":
                eraseWord($(this));
                break;
            case "horizontal":
                if($(this).hasClass("img-text")) {
                    var str_id = $(this).attr("id");
                    str_id = str_id.replace("text", "space");
                    toggleSingleSpace($("#"+str_id), true)
                }
                break;
            case "grammar":
            case "draw":
            case "vertical":
            default:
                return;
        }
    });
    // $("span.text-box").on("hover", function() {
    //     switch(getActiveMode()) {
    //         case "define":
    //             $(this).css("box-shadow", "0px 0px 0px 10px black inset");
    //             setTimeout(function() {
    //                 $(this).css("box-shadow", "none");
    //             }, 500);
    //             break;
    //     }
    // });

    $(".img-block:not(.img-patch) img").on("mousedown", function() {
        mouse_down = true;
        var action;
        switch(getActiveMode()) {
            case "define":
                action = defineWord;
                break;
            case "context":
                action = createContextMap;
                break;
            default:
                return;
        }
        timeout_id = setTimeout(action($(this)), 1000);
    }).on("mouseup mouseleave", function() {
        mouse_down = false;
        switch(getActiveMode()) {
            case "define":
                $(this).popover("hide");
                break;
            case "context":
                break;
            default:
                return;
        }
        clearTimeout(timeout_id);
    });
    // END ACTIVE TOOLS
    
    $("#translate-text").on("click", function() {
        if($(this).is(":checked")) {
            if( $("#ocr-text").is(":checked") ) {
                $("#ocr-text").click();
            }
            $(".img-patch-text").each(function(idx) {
                $(this).val(translation[idx]);
            });
        } else {
            $(".img-patch-text").each(function(idx) {
                $(this).val("");
            });
        }
    });

    $("#ocr-text").on("click", function() {
        if($(this).is(":checked")) {
            if($("#translate-text").is(":checked")) {
                $("#translate-text").click();
            }
            $(".img-patch-text").each(function(idx) {
                $(this).val(ocr[idx]);
            });
        } else {
            $(".img-patch-text").each(function(idx) {
                $(this).val("");
            });
        }
    });

    $("#replace-pronoun").on("click", function() {
        if($(this).is(":checked")) {
            $(".gender-pronoun").show();
        } else {
            fixPronouns();
            if($("#male-pronoun").is("checked")) {
                $("#male-pronoun").click();
            }
            if($("#female-pronoun").is("checked")) {
                $("#female-pronoun").click();
            }
            $(".gender-pronoun").hide();
        }
    });

    $("#male-pronoun").on("click", function() {
        if($(this).is(":checked")) {
            if($("#female-pronoun").is("checked")) {
                $("#female-pronoun").click();
            }
            replacePronouns(false);
        } else {
            fixPronouns();
        }
    });

    $("#female-pronoun").on("click", function() {
        if($(this).is(":checked")) {
            if($("#male-pronoun").is("checked")) {
                $("#male-pronoun").click();
            }
            replacePronouns(true);
        } else {
            fixPronouns();
        }
    });

    $("#vis-container").css("opacity", 1);
    $("#loading").removeClass("show");
});

function toggleMode(elem, close_vertical=false, close_horizontal=false, open_vertical=false, open_horizontal=false) {
    var this_mode = $(elem).data("mode");
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
        var cur_mode = getActiveMode();
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
    var margin_width = ($(".stage").width() - $("#vis-container").width()) / 2.0;
    return margin_width;
}

function setActiveMode(new_mode) {
    for(var type in mode) {
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

function resizeStage() {
    var vp_height = $(window).height();
    var vp_width = $(window).width();
    var stage_height = $("#vis-container").height();
    var stage_width = $("#vis-container").width();
    if($("#context-map-container").height() > stage_height) {
        stage_height = $("#context-map-container").height();
    }
    if(stage_height < vp_height) {
        stage_height = vp_height;
    }
    $(".stage").css("min-height", stage_height * vertical_margin);
    $(".vis").css("min-height", stage_height * vertical_margin);
    var alt_width = $("#context-map-container").width();
    var entity_map_width = $("#entity-map-container").width();
    if(entity_map_width > alt_width && $("#entity-map-container").is(":visible")) {
        alt_width = entity_map_width;
    }
    if($("#context-map-container table").length > 0 || ($("#entity-map-container img").length > 0 && $("#entity-map-container").is(":visible"))) {
        stage_width += (alt_width * 2);
        $("#context-map-container").css("top", $("#1").position().top );
        $("#context-map-container").css("left", $("#vis-container").position().left + $("#1").eq(0).width());
        $("#entity-map-container img").each(function() {
            var text_id = $(this).data("word-id");
            $(this).css("top", $(text_id).parent().parent().position().top + "px");
        });
        $("#entity-map-container").css("left", $("#vis-container").position().left - $("#entity-map-container").width());
    } else {
        stage_width *= horizontal_margin;
    }
    if(stage_width < vp_width) {
        stage_width = vp_width;
    }
    $(".stage").css("min-width", stage_width);
}

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

function getActiveMode() {
    var curr_mode = "";
    for(var key in mode) {
        if(mode.hasOwnProperty(key)) {
            if(mode[key]) {
                curr_mode += key;
            }
        }
    }
    return curr_mode;
}

function eraseWord($elem) {
    var text_id = $elem.attr("id");
    $("#img-text-id").val(text_id);
    var edit_text = $(".custom-text", $("#"+text_id).parent()).html();
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

function fixPronouns() {
    var $blocks = $(".img-text[data-ocr]").filter(function() {
        return $(this).data("ocr") == "him"
            || $(this).data("ocr") == "her"
            || $(this).data("ocr") == "he"
            || $(this).data("ocr") == "she"
            || $(this).data("ocr") == "his"
            || $(this).data("ocr") == "hers";
    });
    for(var i = 0; i < $blocks.length; i++) {
        var $elem = $($blocks[i]);
        var text_id = $elem.attr("id");
        if($elem.css("opacity") < 1) {
            $elem.css("opacity",1);
            $(".custom-text", $("#"+text_id).parent()).html("");
        }
    }
}

function replacePronouns(on) {
    var himher = "his/him";
    var heshe = "he";
    var hishers = "his";
    var new_himher = "her";
    var new_heshe = "she";
    var new_hishers = "her(s)";
    if(!on) {
        himher = "her";
        heshe = "she";
        hishers = "hers";
        new_himher = "his/him";
        new_heshe = "he";
        new_hishers = "his";
    }
    var $blocks = $(".img-text[data-ocr]").filter(function() {
        return $(this).data("ocr") == himher
            || $(this).data("ocr") == heshe
            || $(this).data("ocr") == hishers;
    });

    for(var i=0; i<$blocks.length; i++) {
        $("#img-text-id").val($($blocks[i]).attr("id"));
        var old_text = $($blocks[i]).data("ocr");
        var new_text = "";
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

function injectMetaData() {
    for(var i=0; i<word_blocks.length; i++) {
        for(var y=0; y<word_blocks[i].length; y++) {
            var text = word_blocks[i][y]["text"];
            var idx_block = word_blocks[i][y]["idx_block"];
            var word_pos = word_blocks[i][y]["word_pos"];
            var text_id = "text-" + idx_block.toString() + "-" + word_pos.toString();
            $("#" + text_id).attr("data-ocr", text);
        }
    }
}

function saveText() {
    var text = $("#edit-text").val();    
    var text_id = $("#img-text-id").val();
    $(".custom-text", $("#"+text_id).parent()).html(text);
    $("#"+text_id).css("opacity", 0);
    $("#text-visibility").html("Show Text");
}

function replaceAllText() {
    var text = $("#edit-text").val();
    var text_id = $("#img-text-id").val();
    $(".custom-text", $("#"+text_id).parent()).html(text);
    $("#"+text_id).css("opacity", 0);
    $("#text-visibility").html("Show Text");

    var text_ocr = $("#"+text_id).data("ocr");
    if(text_ocr != "") {
        $(".custom-text", $("img[data-ocr='" + text_ocr + "']").parent()).html(text);
        $("img[data-ocr='" + text_ocr + "']").css("opacity",0);
    }
}

function undoAllText() {
    var text_id = $("#img-text-id").val();
    var $elem = $("#" + text_id);
    $elem.css("opacity",1);
    $("#text-visibility").html("Hide Text");     
    $(".custom-text", $("#"+text_id).parent()).html("");   
    $("#edit-text").val("");
    var text_ocr = $("#"+text_id).data("ocr");
    if(text_ocr != "") {
        $(".custom-text", $("img[data-ocr='" + text_ocr + "']").parent()).html("");
        $("img[data-ocr='" + text_ocr + "']").css("opacity",1);
    }
}

function toggleTextVisibility() {
    var text_id = $("#img-text-id").val();
    var $elem = $("#" + text_id);
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
        var $parent = $elem.parent();
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

function justifyDocument(idx, space_width) {
    $(".img-block").each(function(x){
        if(!$(this).hasClass("img-patch") && $(this).attr("id")==idx) {
            return;
        }
        var $spaces = $("span.text-space.squeeze", $(this));
        if($spaces.length > 0) {
            var added_width = 0;
            var iter_width = space_width;
            while(added_width < space_width) {
                var target_width = Math.floor(space_width/$spaces.length);
                var extra_width = space_width - (target_width*$spaces.length);
                in_transit += $spaces.length;
                $spaces.each(function(i) {
                    var add_width = target_width + $(this).width();
                    var full_width = $(this).data("img-width");
                    if(add_width >= full_width) {
                        $(this).removeClass("squeeze");
                        add_width = full_width;
                    } else {
                        // sneak some of the extra width as we go
                        if(full_width>add_width && extra_width > 0) {
                            var extra_diff = extra_width-(full_width-add_width);
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

function openActiveSpaces() {
    var active_mode = getActiveMode();
    if(active_mode == "horizontal") {
        openSpaces(true);        
    } else if(active_mode == "vertical") {
        openSpaces(false);        
    } else {
        openSpaces(false);
        openSpaces(true);
    }
}

function closeActiveSpaces() {
    var active_mode = getActiveMode();
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
    if(is_horizontal) {
        $(".text-space").removeClass("squeeze");
        in_transit += $(".text-space").length;
        $(".text-space").each(function() {
            space_width = $(this).data("img-width");
            // $(this).width(space_width);
            $(this).transition({width:space_width}, detectResizeStage);
        });
    } else {
        $(".img-patch").removeClass("squeeze");
        in_transit += $(".img-patch").length;
        $(".img-patch").each(function() {
            space_height = $(this).data("img-height");
            if($("#location").is(":checked")) {
                if($(this).data("map-height") > 0) {
                    space_height = $(this).data("map-height");
                }
            }
            // $(this).height(space_height);
            $(this).transition({height:space_height}, detectResizeStage);
        });
    }
}

function closeSpaces( is_horizontal ) {
    if(is_horizontal) {
        in_transit += $(".text-space").length;
        $(".text-space").transition({width:0}, detectResizeStage);
        $(".text-space").addClass("squeeze");
    } else {
        in_transit += $(".img-patch").length;
        $(".img-patch").transition({height:0}, detectResizeStage);
        $(".img-patch").addClass("squeeze");        
    }
}

function detectResizeStage() {
    in_transit--;
    if(in_transit == 0) {
        resizeStage();
    }
}

function drawUniqueness() {
    var min_width = 9999;
    $(".img-block.img-patch").each(function(idx_curr) {
        var idx = idx_curr+1;
        var $chart = $("div.uniqueness-chart", this);
        for(var i=0; i<ngram_plot.length; i++) {
            if(ngram_plot[i]["idx_block"] == idx) {
                var idx_word = ngram_plot[i]["idx_word"];
                var width = word_blocks[idx][idx_word]["width"].toString();
                var left = word_blocks[idx][idx_word]["x"].toString();
                if(width<min_width) {
                    min_width = width;
                }
                $chart.append("<span id='unique-" + idx.toString() + "-" + idx_word.toString()
                    + "' style='height:0px;bottom:0px;left:" + left + "px;width:" + width + "px;'></span>");
            }
        }
    });
    if(min_width > 20) {
        min_width = 20;
    }
    $(".img-block.img-patch div.uniqueness-chart span").width(min_width);
}

function argsort(to_sort) {
    for (var i = 0; i < to_sort.length; i++) {
      to_sort[i] = [to_sort[i], i];
    }
    to_sort.sort(function(left, right) {
      return left[0] > right[0] ? -1 : 1;
    });
    to_sort.sort_indices = [];
    for (var j = 0; j < to_sort.length; j++) {
      to_sort.sort_indices.push(to_sort[j][1]);
      to_sort[j] = to_sort[j][0];
    }
    return to_sort;
}

function setUniqueness(dateval) {
    var idx_date = dateval - 1800;
    var usage_list = [];
    for(var i=0; i<ngram_plot.length; i++) {
        usage_list.push(ngram_plot[i]["usage"][idx_date]);
    }
    usage_list = argsort(usage_list);

    for(var rank=0; rank<usage_list.length; rank++) {
        var i = usage_list.sort_indices[rank];
        var norm_rank = rank;
        if (rank > 0) {
            var last_rank = rank-1;
            var last_idx = usage_list.sort_indices[last_rank];
            while(ngram_plot[i]["usage"][idx_date] == ngram_plot[last_idx]["usage"][idx_date] && last_rank > 0) {
                last_rank--;
                last_idx = usage_list.sort_indices[last_rank];
            }
            norm_rank = last_rank;
        }
        var idx_block = ngram_plot[i]["idx_block"];
        var idx_word = ngram_plot[i]["idx_word"];
        var id = "unique-" + idx_block.toString() + "-" + idx_word.toString();
        var patch_height = $("#"+id).closest("div.img-patch").data("img-height");
        var img_url = "uniqueness_0.png";
        var image_rank = (norm_rank/usage_list.length);

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

function drawConfidence() {
    for(var i=0; i<word_blocks.length; i++) {
        for(var j=0; j<word_blocks[i].length; j++) {
            var opacity = (word_blocks[i][j]["confidence"]/100.0);
            opacity = (1.00-Math.max((Math.round(opacity * 5) / 5), 0.1)).toFixed(2) * 0.9;
            var idx_block = word_blocks[i][j]["idx_block"];
            var idx_word = word_blocks[i][j]["word_pos"];
            var text_id = "#text-" + idx_block.toString() + "-" + idx_word.toString();
            var $conf = $("<div/>", {"class":"text-confidence"});
            $conf.css("opacity", opacity);
            $conf.width(word_blocks[i][j]["width"]);
            $conf.height(word_blocks[i][j]["height"]);
            $conf.css("top", word_blocks[i][j]["y"] + "px");
            if(idx_word == 0) {
                $conf.css("left", word_blocks[i][j]["x"] + "px");                
            }
            $(text_id).parent().append($conf);
        }
    }
}

function drawNGramUsage() {
    $(".img-block.img-patch").each(function(idx_curr) {
        var idx = idx_curr+1;
        var canvas = $("canvas.ngram-usage", this)[0];
        var ctx = canvas.getContext("2d");
        ctx.canvas.width = $(this).width();
        ctx.canvas.height = $(this).data("img-height");
        for(var i=0; i<ngram_plot.length; i++) {
            if(ngram_plot[i]["idx_block"] == idx) {
                idx_word = ngram_plot[i]["idx_word"];
                ctx.beginPath();                
                var img = new Image();
                img.coords = {x:word_blocks[idx][idx_word]["x"],y:0};
                img.onload = function() {
                    ctx.drawImage(this, this.coords.x, this.coords.y);
                };
                img.src = "data:image/png;base64,"+ngram_plot[i]["ngram"];
            }
        }
    });
}

function drawLocations() {
    for(var i=0; i<word_blocks.length; i++) {
        for(var j=0; j<word_blocks[i].length; j++) {
            if(word_blocks[i][j]["label"] == "GPE") {
                // draw the overlay color box
                var idx_block = word_blocks[i][j]["idx_block"];
                var idx_word = word_blocks[i][j]["word_pos"];
                var text_id = "#text-" + idx_block.toString() + "-" + idx_word.toString();
                var $loc = $("<div/>", {"class":"entity-location"});
                $loc.width(word_blocks[i][j]["width"]);
                $loc.height(word_blocks[i][j]["height"]);
                $loc.css("top", word_blocks[i][j]["y"] + "px");
                if(idx_word == 0) {
                    $loc.css("left", word_blocks[i][j]["x"] + "px");                
                }
                $(text_id).parent().append($loc);
                // draw the map
                var $img = new Image();
                $img.src = "data:image/png;base64,"+word_blocks[i][j]["map"];
                $($img).css("top", $(text_id).parent().parent().position().top + "px");
                $($img).data("word-id",text_id);
                $("#entity-map-container").append($img);
            }
        }
    }
    // $(".img-block:not(.img-patch)").each(function(idx) {
    //     var canvas = $("canvas.entity-location", this)[0];
    //     var ctx = canvas.getContext("2d");
    //     var height = $(this).height();
    //     ctx.canvas.width = $(this).width();
    //     ctx.canvas.height = height + map_height;
    //     ctx.canvas.style.top = "-" + map_height + "px";
    //     for(var i=0; i<word_blocks[idx].length; i++) {
    //         if(word_blocks[idx][i]["label"] == "GPE") {
    //             ctx.beginPath();
    //             ctx.fillStyle = "rgba(53, 153, 66, 0.5)";
    //             ctx.fillRect(word_blocks[idx][i]["x"], word_blocks[idx][i]["y"] + map_height, word_blocks[idx][i]["width"], height);
    //             var img = new Image();
    //             img.coords = {x:word_blocks[idx][i]["map_x"],y:0};
    //             img.onload = function() {
    //                 ctx.drawImage(this, this.coords.x, this.coords.y);
    //             };
    //             img.src = "data:image/png;base64,"+word_blocks[idx][i]["map"];
    //         }
    //     }
    // });
}

function init() {
    canvas = document.getElementById('draw-board');
    ctx = canvas.getContext("2d");
    canvas.width=$(".vis").width();
    canvas.height=$(".vis").height();
    $("#draw-board").width(canvas.width);
    $("#draw-board").height(canvas.height);
    w = canvas.width;
    h = canvas.height;
    
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

function textColor(obj) {
    $("#text-color-select").css("background-color", obj.id);
    $(".img-patch-text").css("color", obj.id);
    $(".custom-text").css("color", obj.id);
}

function color(obj) {
    $("#draw-color-select").css("background-color", obj.id);

    switch (obj.id) {
        case "#D93240":
            x = "#D93240";
            break;
        case "#638CA6":
            x = "#638CA6";
            break;
        case "#BFD4D9":
            x = "#BFD4D9";
            break;
        case "#0F5959":
            x = "#0F5959";
            break;
        case "#17A697":
            x = "#17A697";
            break;
        case "black":
            x = "black";
            break;
        case "white":
            x = "white";
            break;
    }
    if (x == "white") y = 14;
    else y = 2;

}

function draw() {
    ctx.beginPath();
    ctx.moveTo(prevX, prevY);
    ctx.lineTo(currX, currY);
    ctx.strokeStyle = x;
    ctx.lineWidth = y;
    ctx.stroke();
    ctx.closePath();
}

function erase() {
    var m = confirm("Are you sure you would like to clear?");
    if (m) {
        ctx.clearRect(0, 0, w, h);
        // document.getElementById("canvasimg").style.display = "none";
    }
}

function print() {
    html2canvas($(".vis"), {
        onrendered: function (canvas) {
            // Convert and download as image 
            Canvas2Image.saveAsPNG(canvas);
        }
    });
}

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