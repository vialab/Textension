var canvas, ctx, flag = false,
prevX = 0,
currX = 0,
prevY = 0,
currY = 0,
dot_flag = false,
x = "black",
y = 2,
map_height = 150,
drawing = false,
removing = false,
haslistener=false;

$(document).ready(function() {   
    $(".img-block:not(.img-patch)").on("click", function() {
        if(drawing || removing) return;

        var i = parseInt($(this).attr("id"));
        if(i == 0) {
            return;
        }
        toggleSpace($("#"+i.toString()+".img-patch"))
    });
    injectMetaData();

    drawConfidence();
    $("canvas.text-confidence").hide();
    $("#confidence").on("click", function() {
        if($(this).is(":checked")) {
            $("canvas.text-confidence").show();            
        } else {
            $("canvas.text-confidence").hide();            
        }
    });

    drawUniqueness();
    $("#uniqueness-range").hide();
    $("#uniqueness").on("click", function() {
        if($(this).is(":checked")) {
            openSpaces();
            setUniqueness( $("#uniqueness-range input").val() );
            $("#uniqueness-range").show();
        } else {
            $("div.uniqueness-chart span").height(0);
            $("#uniqueness-range").hide();
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
            openSpaces();            
            $("canvas.ngram-usage").show();        
        } else {
            $("canvas.ngram-usage").hide();            
        }
    });

    drawLocations();    
    $("canvas.entity-location").hide();
    $("#location").on("click", function() {
        if($(this).is(":checked")) {
            openSpaces();
            $("canvas.entity-location").show();
        } else {
            $("canvas.entity-location").hide();
            openSpaces();
        }
    });

    $("#draw-tool").on("click", function() {
        if($(this).is(":checked")) {
            if($("#remove-word").is(":checked")) {
                $("#remove-word").click();
            }
            drawing = true;
            $("canvas#draw-board").removeClass("overlay");
            $("#draw-options").show();
            if(!haslistener) init();
        } else {
            drawing = false;
            $("canvas#draw-board").addClass("overlay");
            $("#draw-options").hide();
        }
    });

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

    $("#remove-word").on("click", function() {
        if($(this).is(":checked")) {
            if( $("#draw-tool").is(":checked") ) {
                $("#draw-tool").click();
            }
            closeSpaces();
            removing = true;
        } else {
            removing = false;
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

    $(".img-block:not(.img-patch) img").on("click", function() {
        if(drawing || !removing) return;
        if(removing) {
            var text_id = $(this).attr("id");
            $("#img-text-id").val(text_id);
            var edit_text = $(".custom-text", $("#"+text_id).parent()).html();
            $("#edit-text").val(edit_text);
            updateSampleText();
            $("#edit-text").height($(this).height());
            $("#edit-text").width($(this).width());
            $("#sample-text-box").height($(this).height());
            $("#sample-text-box").width($(this).width());
            $("#text-edit").modal("show");
            if($(this).css("opacity") > 0) {
                $("#text-visibility").html("Hide Text");
            } else {
                $("#text-visibility").html("Show Text");
            }
        }
    });

    $("#edit-text").on("input", function() {
        updateSampleText();
    });
});

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

function updateSampleText() {
    var text = $("#edit-text").val();
    $("#sample-text-box").html(text);
}

function saveText() {
    var text = $("#edit-text").val();    
    var text_id = $("#img-text-id").val();
    $(".custom-text", $("#"+text_id).parent()).html(text);
    $("#"+text_id).css("opacity", 0);
    $("#text-visibility").html("Show Text");
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
        updateSampleText();
    }
}

function toggleSpace($elem) {
    if($elem.hasClass("squeeze")) {
        $elem.removeClass("squeeze");
        space_height = $elem.data("img-height");
        if($("#location").is(":checked")) {
            if($elem.data("map-height") > 0) {
                space_height = $elem.data("map-height");
            }
        }
        $elem.height(space_height);
    } else {
        $elem.height(0);
        $elem.addClass("squeeze");        
    }
}

function openSpaces() {
    if(drawing || removing) return;
    $(".img-patch").removeClass("squeeze");
    $(".img-patch").each(function() {
        space_height = $(this).data("img-height");
        if($("#location").is(":checked")) {
            if($(this).data("map-height") > 0) {
                space_height = $(this).data("map-height");
            }
        }
        $(this).height(space_height);
    });
}

function closeSpaces() {
    if(drawing || removing) return;    
    $(".img-patch").height(0);
    $(".img-patch").addClass("squeeze");    
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
        var new_height = (patch_height/usage_list.length) * norm_rank;
        if(new_height == 0) { new_height = 1; }
        $("#"+id).height(new_height);
    }
}

function drawConfidence() {
    $(".img-block:not(.img-patch)").each(function(idx) {
        var canvas = $("canvas.text-confidence", this)[0];
        var ctx = canvas.getContext("2d");
        ctx.canvas.width = $(this).width();
        ctx.canvas.height = $(this).height();
        for(var i=0; i<word_blocks[idx].length; i++) {
            var opacity = (word_blocks[idx][i]["confidence"]/100.0);
            ctx.beginPath();
            ctx.fillStyle = "rgba(244, 167, 66, " + opacity + ")";
            ctx.fillRect(word_blocks[idx][i]["x"], word_blocks[idx][i]["y"], word_blocks[idx][i]["width"], 20);
        }
    });
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
    // https://maps.googleapis.com/maps/api/staticmap?center={text}*zoom=4&size=150x100
    $(".img-block:not(.img-patch)").each(function(idx) {
        var canvas = $("canvas.entity-location", this)[0];
        var ctx = canvas.getContext("2d");
        var height = $(this).height();
        ctx.canvas.width = $(this).width();
        ctx.canvas.height = height + map_height;
        ctx.canvas.style.top = "-" + map_height + "px";
        for(var i=0; i<word_blocks[idx].length; i++) {
            if(word_blocks[idx][i]["label"] == "GPE") {
                ctx.beginPath();
                ctx.fillStyle = "rgba(53, 153, 66, 0.5)";
                ctx.fillRect(word_blocks[idx][i]["x"], word_blocks[idx][i]["y"] + map_height, word_blocks[idx][i]["width"], height);
                var img = new Image();
                img.coords = {x:word_blocks[idx][i]["map_x"],y:0};
                img.onload = function() {
                    ctx.drawImage(this, this.coords.x, this.coords.y);
                };
                img.src = "data:image/png;base64,"+word_blocks[idx][i]["map"];
            }
        }
    });
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