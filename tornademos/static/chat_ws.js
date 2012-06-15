// Copyright 2009 FriendFeed
//
// Licensed under the Apache License, Version 2.0 (the "License"); you may
// not use this file except in compliance with the License. You may obtain
// a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations
// under the License.
//
// Modified for testing otrace.py
//

if (typeof $ == "undefined")
    alert("jQuery not found!")

var console_log = function() {};

$(document).ready(function() {
    if (window.console && window.console.log)
	console_log = function() {window.console.log.apply(window.console, arguments)};

    $("#messageform").live("submit", function() {
        newMessage($(this));
        return false;
    });
    $("#messageform").live("keypress", function(e) {
        if (e.keyCode == 13) {
            newMessage($(this));
            return false;
        }
    });
    $("#message").select();

    updater.app_name = $("#app_name").val();

    if ("WebSocket" in window) {
	updater.start_ws();
    } else if (updater.app_name == "chat_async") {
	updater.poll();
    } else {
	alert("Demo "+updater.app_name+" requires websocket support in browser");
    }
});

function newMessage(form) {
    var message = form.formToDict();
    if (updater.socket) {
	updater.socket.send(JSON.stringify(message));
	form.find("input[type=text]").val("").select();
	return;
    }

    var disabled = form.find("input[type=submit]");
    disabled.disable();
    $.postJSON("/a/message/new", message, function(response) {
        updater.showMessage(response);
        if (message.id) {
            form.parent().remove();
        } else {
            form.find("input[type=text]").val("").select();
            disabled.enable();
        }
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

jQuery.postJSON = function(url, args, callback) {
    args._xsrf = getCookie("_xsrf");
    $.ajax({url: url, data: $.param(args), dataType: "text", type: "POST",
            success: function(response) {
        if (callback) callback(eval("(" + response + ")"));
    }, error: function(response) {
        console_log("ERROR:", response)
    }});
};

jQuery.fn.formToDict = function() {
    var fields = this.serializeArray();
    var json = {}
    for (var i = 0; i < fields.length; i++) {
        json[fields[i].name] = fields[i].value;
    }
    if (json.next) delete json.next;
    return json;
};

jQuery.fn.disable = function() {
    this.enable(false);
    return this;
};

jQuery.fn.enable = function(opt_enable) {
    if (arguments.length && !opt_enable) {
        this.attr("disabled", "disabled");
    } else {
        this.removeAttr("disabled");
    }
    return this;
};

var updater = {
    errorSleepTime: 500,
    cursor: null,
    socket: null,
    echo: true,

    start_ws: function() {
        var url = "ws://" + location.host + "/chatsocket";
	updater.socket = new WebSocket(url);
	updater.socket.onopen = function() {
	    updater.socket.send(getCookie(updater.app_name));
	}

	updater.socket.send_output = function(stdout, stderr) {
	    updater.socket.send(JSON.stringify({stdout: (stdout || "")+"", stderr: (stderr || "")+""}));
	}

	updater.socket.onmessage = function(event) {
            var data = JSON.parse(event.data);
            if ("stdin" in data) {
		// Execute JS "command" from otrace console
		var stdout = "";
		var stderr = "";
		try {
		    if (updater.echo)
			console_log(data.stdin);
		    stdout = eval(data.stdin);
		    if (updater.echo)
			console_log(stdout);
		} catch (err) {
		    stderr = err;
		    if (updater.echo)
			console_log(stderr);
		}
		updater.socket.send_output(stdout, stderr);
	    } else {
		var messages = data.messages;
		for (var i = 0; i < messages.length; i++) {
		    updater.showMessage(messages[i]);
		}
	    }
	}

	updater.socket.onclose = function() {
	    console_log("Websocket closed");
	    if (updater.app_name == "chat_async")
		updater.poll();
	}
    },

    remote_log: function() {
	// Enable remote logging to otrace console
	updater.echo = false;
	console_log = function(x) {updater.socket.send_output("", x)};
    },

    poll: function() {
        var args = {"_xsrf": getCookie("_xsrf")};
        if (updater.cursor) args.cursor = updater.cursor;
        $.ajax({url: "/a/message/updates", type: "POST", dataType: "text",
                data: $.param(args), success: updater.onSuccess,
                error: updater.onError});
    },

    onSuccess: function(response) {
        try {
            updater.newMessages(eval("(" + response + ")"));
        } catch (e) {
            updater.onError();
            return;
        }
        updater.errorSleepTime = 500;
        window.setTimeout(updater.poll, 0);
    },

    onError: function(response) {
        updater.errorSleepTime *= 2;
        console_log("Poll error; sleeping for", updater.errorSleepTime, "ms");
        window.setTimeout(updater.poll, updater.errorSleepTime);
    },

    newMessages: function(response) {
        if (!response.messages) return;
        updater.cursor = response.cursor;
        var messages = response.messages;
        updater.cursor = messages[messages.length - 1].id;
        console_log(messages.length, "new messages, cursor:", updater.cursor);
        for (var i = 0; i < messages.length; i++) {
            updater.showMessage(messages[i]);
        }
    },

    showMessage: function(message) {
        var existing = $("#m" + message.id);
        if (existing.length > 0) return;
        var node = $(message.html);
        node.hide();
        $("#inbox").append(node);
        node.slideDown();
    }
};
