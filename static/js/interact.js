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
haslistener=false;

$(document).ready(function() {
    $(".img-block:not(.img-patch)").on("click", function() {
        if(drawing) return;

        var i = parseInt($(this).attr("id"));
        if(i == 0) {
            return;
        }
        toggleSpace($("#"+i.toString()+".img-patch"))
    });

    drawConfidence();
    $("canvas.text-confidence").hide();
    $("#confidence").on("click", function() {
        if($(this).is(":checked")) {
            $("canvas.text-confidence").show();            
        } else {
            $("canvas.text-confidence").hide();            
        }
    });

    drawNGramUsage();
    $("canvas.ngram-usage").hide();
    $("#ngram").on("click", function() {
        if($(this).is(":checked")) {
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
            closeSpaces();
            $("canvas.entity-location").hide(); 
        }
    });

    $("#draw-tool").on("click", function() {
        if($(this).is(":checked")) {
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
}); 

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
    if(drawing) return;
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
    if(drawing) return;    
    $(".img-patch").height(0);
    $(".img-patch").addClass("squeeze");    
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
}

function color(obj) {
    $("#draw-color-select").css("background-color", obj.id);

    switch (obj.id) {
        case "green":
            x = "green";
            break;
        case "blue":
            x = "blue";
            break;
        case "red":
            x = "red";
            break;
        case "yellow":
            x = "yellow";
            break;
        case "orange":
            x = "orange";
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