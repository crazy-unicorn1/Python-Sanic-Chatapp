// 缓存机制
var foowwLocalStorage = {
  set: function (key, value, ttl_ms) {
    var data = { value: value, expirse: new Date(ttl_ms).getTime() };
    localStorage.setItem(key, JSON.stringify(data));
  },
  get: function (key) {
    var data = JSON.parse(localStorage.getItem(key));
    if (data !== null) {
      debugger;
      if (data.expirse != null && data.expirse < new Date().getTime()) {
        localStorage.removeItem(key);
      } else {
        return data.value;
      }
    }
    return null;
  },
};

function websocket_emit(ws, event_id, data) {
  if (ws.readyState === WebSocket.OPEN) {
    sendData = {
      event_id,
      data,
    };
    ws.send(JSON.stringify(sendData));
    // Perform WebSocket operations
  } else {
    console.log("WebSocket is not in OPEN state.");
  }
}

// 获取连接状态 socket_app.connected
//连接成功
var socket_app = null;

const _charStr =
  "abacdefghjklmnopqrstuvwxyzABCDEFGHJKLMNOPQRSTUVWXYZ0123456789";

// 客户端类型
var ClientTypes = {
  PC: "pc",
  Mobile: "mobile",
};
// 在线类型
var OnlineStatu = {
  online: "online",
  bebusy: "bebusy",
  offline: "offline",
};
// 浏览器类型
var BrowserTypes = {
  Chrome: "chrome",
  Firefox: "firefox",
  Edge: "edge",
};
// 系统类型
var SystemTypes = {
  windows: "windows",
  linux: "linux",
  macos: "macos",
};
// 会话状态
var ConversationStatu = {
  normal: "normal",
  waiting: "waiting",
  finished: "finished",
};
// 内容类型
var ContentTypes = {
  TEXT: "text",
  VIDEO: "video",
  PICTURE: "picture",
  FILE: "file",
};

function getShiQuTime(msgtime) {
  let timezoneOffset = 0 - new Date().getTimezoneOffset() / 60;
  let ddl = msgtime.replace(/-/g, "/");
  let dvv = new Date(ddl);
  const TODAY = new Date(dvv.setHours(dvv.getHours() + timezoneOffset));
  return formatDate(TODAY, "MM-dd hh:mm");
}

$(function () {
  // 日期选择器
  $.picker_YY_HH_DD_HH_MM_SS(".pickerdate");
  // 年月日选择器
  $.single_YY_MM_DD(".selectDateYMD");

  $(".stateBox").on("click", function () {
    if ($(".stateSelect").hasClass("show")) {
      $(".stateSelect").removeClass("show");
    } else {
      $(".stateSelect").addClass("show");
    }
  });

  // 显示状态选项
  $(".stateSelect").on({
    mouseover: function () {
      $(this).addClass("show");
    },
    mouseout: function () {
      $(".stateSelect").removeClass("show");
    },
  });

  // 菜单定位

  // 监控点击菜单
  $(".navItem").on("click", function (e) {
    e.stopPropagation();
    $(this).addClass("active");
    $(this).siblings().removeClass("active");
    let page_code = $(this).find("a").attr("href").replace("#", "");
    loading_html(page_code);
  });

  /*选项菜单*/
  $("body").on("click", ".sc-tab-title li", function () {
    let ftag = $(this).parent().parent();
    let index = ftag.find(".sc-tab-title").find("li").index(this);
    $(this).siblings().removeClass("sc-this");
    $(this).addClass("sc-this");
    ftag.find(".sc-tab-item").removeClass("sc-show");
    ftag.find(".sc-tab-item").eq(index).addClass("sc-show");
  });

  function send_ping() {
    websocket_emit(socket_app, "ping", "ping");
  }

  let pingTimerId = 0;

  function setupWebSocket() {
    var _con_params = "crrServiceId=" + service_id + "&siteCode=" + site_code;
    //var socket_app = io.connect(location.protocol + '//' + document.domain + '/serviceChat', {transports: ['websocket'], 'query': _con_params});
    socket_app = new WebSocket(
      `${location.protocol.replace("http", "ws")}//${document.domain}:${
        location.port
      }/serviceChat?${_con_params}`
    );

    socket_app.onopen = function () {
      let crrtiem = new Date();
      console.log("WEbsocket is connected", crrtiem);
      let init_data = {
        service_id: service_id,
      };
      websocket_emit(socket_app, "serviceInit", init_data);
      pingTimerId = setInterval(send_ping, 50000);

      if (window.location.href.indexOf("#") > -1) {
        var a_tags = $(".navItem").find("a");
        a_tags.each(function (index, data) {
          if (window.location.href.endsWith($(this).attr("href")) === true) {
            $(this).parent().siblings().removeClass("active");
            $(this).parent().addClass("active");
            let page_code = $(this).attr("href").split("#").pop();
            loading_html(page_code);
          }
        });
      } else {
        $(".navList").find(".home").addClass("active");
        loading_html("home");
      }
    };

    socket_app.onclose = function () {
      console.log("WebSocket connection closed");
      clearInterval(pingTimerId);
      setTimeout(setupWebSocket, 1000);
    };

    socket_app.onmessage = (event) => {
      const jsonData = JSON.parse(event.data);
      event_id = jsonData.event_id;
      msg = jsonData.msg;

      switch (event_id) {
        case "serviceReceiveInit":
          socket_serviceReceiveInit(msg);
          break;
        case "chatWdTotalCount":
          socket_chatWdTotalCount(msg);
          break;
        case "chatNewConversationNewReceive":
          socket_chatNewConversationNewReceive(msg);
          break;
        case "chatConversationList":
          socket_chatConversationList(msg);
          break;
        case "chatConversationInfo":
          socket_chatConversationInfo(msg);
          break;
        case "chatCtnOnlineCount":
          socket_chatCtnOnlineCount(msg);
          break;
        case "chatNewConversation":
          socket_chatNewConversation(msg);
          break;
        case "ChatServerSideMessage":
          socket_ChatServerSideMessage(msg);
          break;
        case "ServerSideUploadFeedback":
          socket_ServerSideUploadFeedback(msg);
          break;
        case "chatFinishConversation":
          socket_chatFinishConversation(msg);
          break;
        case "serviceFinishList":
          socket_serviceFinishList(msg);
          break;
        case "serverFeedback":
          socket_serverFeedback(msg);
          break;
        case "serviceConversationList":
          socket_serviceConversationList(msg);
          break;
        case "ServerReceiveConversationTotal":
          socket_ServerReceiveConversationTotal(msg);
          break;
        case "receiveTsConversationMsg":
          socket_receiveTsConversationMsg(msg);
          break;
        case "receiveOnlieUpload":
          socket_receiveOnlieUpload(msg);
          break;
        case "monitorCommand":
          socket_monitorCommand(msg);
          break;
        case "receviceUploadInfoCard":
          socket_receviceUploadInfoCard(msg);
          break;
        case "pong":
          console.log("pong is received...");
          break;
        default:
          console.log("Unknown event ID:", jsonData.event_id);
          break;
      }
    };
  }
  setupWebSocket();

  // 接收初始化数据
  function socket_serviceReceiveInit(msg) {
    if (msg.code !== 200) {
      xtalert.alertError("您的账户已在别处登录！请重新登录！");
      let tt = setTimeout(function () {
        window.location.href = outUrl;
      }, 1000);
      return;
    }
    let back_data = msg.data;
    let wdToaslCount = back_data.wdToaslCount;
    let totalWdNumber_obj = $("#totalWdNumber");
    if (wdToaslCount > 0) {
      totalWdNumber_obj.show();
      totalWdNumber_obj.text(wdToaslCount);
    }
    let leavingCount = back_data.leavingCount;
    let leavingCount_obj = $("#leavingCount");
    if (leavingCount > 0) {
      leavingCount_obj.show();
      leavingCount_obj.text(leavingCount);
    }
    if ($(".onlineTotalCount").length > 0) {
      $(".onlineTotalCount span").text(back_data.onlineTotal);
    }
    if ($(".crrOnlineCount").length > 0) {
      $(".crrOnlineCount span").text(back_data.onlinePresent);
    }
  }

  // 获取当前客服未读信息数量
  function socket_chatWdTotalCount(msg) {
    let wdToaslCount = msg.wdToaslCount;
    $("#totalWdNumber").text(wdToaslCount);
  }

  // 接收最新会话信息
  function socket_chatNewConversationNewReceive(msg) {
    if (msg.crr_service_id === service_id) {
      if (beep_switch) {
        let mp3ll = new Audio("/public/chat/mp3/chatls.mp3"); // 创建音频对象
        mp3ll.loop = false;
        mp3ll.play(); // 播放
      }
      if ($(".customerList").length > 0) {
        // 检测当前是否聊天页面
        let conversation_id = msg.conversation_id;
        let result_ls = ChackWinConversationId(conversation_id);
        const crrWinObj = result_ls[0];
        const crrIdwinSatte = result_ls[1];
        if (crrIdwinSatte) {
          const chatContentObj = crrWinObj.find(".chatContent");
          let newHtml = "";
          if (msg.content_type === "text") {
            newHtml +=
              '<div class="chat-block chatL">' +
              '<div class="inside">' +
              '<div class="userImage">' +
              '<span class="iconfont icon-windows-fill" style="font-size: 23px;"></span>' +
              "</div>" +
              '<div class="chat-name">' +
              msg.customer_name +
              '<span class="time">' +
              getShiQuTime(msg.create_time) +
              "</span>" +
              "</div>" +
              '<div class="chatting-content">' +
              '<div class="conBox">' +
              msg.text;
            if (msg.translate_text) {
              newHtml +=
                '<div class="translateText">' + msg.translate_text + "</div>";
            }
            newHtml += "</div>";
            if (msg.translate_state && !msg.translate_text) {
              newHtml +=
                '<span class="translateBtn" onclick="translateText_func($(this),\'' +
                msg.content_id +
                '\')"><i class="iconfont icon-fanyi3"></i></span>';
            }
            newHtml += "</div></div></div>";
          } else if (msg.content_type === "picture") {
            newHtml +=
              '<div class="chat-block chatL">' +
              '<div class="inside">' +
              '<div class="userImage">' +
              '<span class="iconfont icon-windows-fill" style="font-size: 23px;"></span>' +
              "</div>" +
              '<div class="chat-name">' +
              msg.customer_name +
              '<span class="time">' +
              getShiQuTime(msg.create_time) +
              "</span>" +
              "</div>" +
              '<div class="chatting-content">' +
              '<div class="conBox contentImage">' +
              '<a href="' +
              msg.file_path +
              '">' +
              '<img src="' +
              msg.file_path +
              '" alt="" style="width: 100%; display: inline-block;">' +
              "</a></div></div></div></div>";
          } else if (msg.content_type === "video") {
            newHtml +=
              "" +
              '                    <div class="chat-block chatL">\n' +
              '                        <div class="inside">\n' +
              '                            <div class="userImage">\n' +
              '                                <span class="iconfont icon-windows-fill" style="font-size: 23px;"></span>\n' +
              "                            </div>\n" +
              '<div class="chat-name">' +
              msg.customer_name +
              '<span class="time">' +
              getShiQuTime(msg.create_time) +
              "</span>" +
              "</div>" +
              '                            <div class="chatting-content">\n' +
              '                                       <video width="400" height="auto" controls> ' +
              "<source src='" +
              msg.file_path +
              '\' type="video/mp4"/>' +
              "</video>" +
              "                            </div>\n" +
              "                        </div>\n" +
              "                    </div>";
          }
          chatContentObj.append(newHtml);
          baguetteBox.run(".chatContent");
          let cttCon = $("#" + conversation_id);
          chatContentObj.scrollTop(chatContentObj[0].scrollHeight);
          websocket_emit(socket_app, "chatMessageReadState", {
            content_id: msg.content_id,
          });

          let data_wdState = cttCon.attr("data-wdState");
          if (data_wdState === "0") {
            cttCon.attr("data-wdState", "1");
            timing_func(
              cttCon,
              msg.djs_h,
              msg.djs_m,
              msg.djs_s,
              conversation_id,
              false
            );
          }
        } else {
          let cttCon = $("#" + conversation_id);
          let lowWdCount = parseInt(cttCon.attr("data-wdCount"));
          cttCon.attr("data-wdCount", lowWdCount + 1);
          cttCon
            .find(".CmItemnlineNumber")
            .text((lowWdCount + 1).toString())
            .show();
          cttCon.insertAfter($(".selectMyTs"));

          let totalWdNumber_obj = $("#totalWdNumber");
          let low_tt = $.trim(totalWdNumber_obj.text());
          totalWdNumber_obj.text((parseInt(low_tt) + 1).toString());
          totalWdNumber_obj.show();

          let data_wdState = cttCon.attr("data-wdState");
          if (data_wdState === "0") {
            cttCon.attr("data-wdState", "1");
            timing_func(
              cttCon,
              msg.djs_h,
              msg.djs_m,
              msg.djs_s,
              conversation_id,
              false
            );
          }
        }
      } else {
        let totalWdNumber_obj = $("#totalWdNumber");
        let low_tt = $.trim(totalWdNumber_obj.text());
        totalWdNumber_obj.text((parseInt(low_tt) + 1).toString());
        totalWdNumber_obj.show();
      }

      if (msg.is_automatic) {
        let dataUid = msg.dataUid;
        let messageContent = msg.auto_reply;
        let conversation_id = msg.conversation_id;
        if (!messageContent || !conversation_id) {
          return "";
        }

        let _data = {
          service_id: service_id,
          conversation_id: conversation_id,
          text: messageContent,
          temporary_data_id: dataUid,
          is_problem: true,
          is_automatic: true,
          action: "sendProblemMsg",
        };
        let crr_time = new Date();
        let daTime = formatDate(crr_time, "MM-dd hh:mm");
        let crrWinObj;
        let crrIdwinSatte = false;
        if ($("#chatWindowOneConversationId").val() === conversation_id) {
          crrIdwinSatte = true;
          crrWinObj = $("#chatWindowOne");
        } else if (
          $("#chatWindowTwoConversationId").val() === conversation_id
        ) {
          crrIdwinSatte = true;
          crrWinObj = $("#chatWindowTwo");
        } else if (
          $("#chatWindowThreeConversationId").val() === conversation_id
        ) {
          crrIdwinSatte = true;
          crrWinObj = $("#chatWindowThree");
        }
        const crrStamp = parseInt(Date.now() / 1000);
        if (crrIdwinSatte) {
          let crrhtml =
            '<div class="chat-block chatR" data-timeStamp="' +
            crrStamp +
            '"' +
            ' data-temporary-uuid="' +
            dataUid +
            '">' +
            '<div class="inside">' +
            '<img src="' +
            service_portrait +
            '" alt="" class="userImage">' +
            '<div class="chat-name">' +
            service_name +
            '<span class="time">' +
            daTime +
            "</span>" +
            "</div>" +
            '<div class="chatting-content">' +
            '<span class="msgStatu"><i class="iconfont icon-jiazai2"></i></span>' +
            '<div class="conBox">' +
            messageContent +
            "</div>" +
            "</div></div></div>";
          const chatContetnObj = crrWinObj.find(".chatContent");
          chatContetnObj.append(crrhtml);
          chatContetnObj.scrollTop(chatContetnObj[0].scrollHeight);
        }
        websocket_emit(socket_app, "problemServiceMsg", _data);
        // let _data = {'service_id': msg.crr_service_id, 'conversation_id': conversation_id, 'text': messageContent, 'temporary_data_id': crrUuid}
        // websocket_emit(socket_app, 'customerServiceMsg', _data)
        // var crrWinObj = $('input[value="' + conversation_id + '"]').parent();
        //
        // let crr_time = new Date();
        // let daTime = formatDate(crr_time, 'MM-dd hh:mm');
        // const crrStamp = parseInt(Date.now()/1000);
        // let crrhtml = '<div class="chat-block chatR" data-timeStamp="' + crrStamp + '"' + ' data-temporary-uuid="' + crrUuid  + '" data-msgStatu="0">' +
        //     '<div class="inside">' +
        //         '<img src="' + service_portrait + '" alt="" class="userImage">' +
        //         '<div class="chat-name">' + service_name +
        //         '<span class="time">' + daTime + '</span>' +
        //         '</div>' +
        //         '<div class="chatting-content">' +
        //             '<span class="msgStatu"><i class="iconfont icon-jiazai2"></i></span>' +
        //             '<div class="conBox">' + messageContent + '</div>' +
        //             '<div class="retract_message">撤回消息</div>' +
        //         '</div></div></div>'
        //
        // const cagtContentObj = crrWinObj.find(".chatContent");
        // cagtContentObj.append(crrhtml);
        // cagtContentObj.scrollTop(cagtContentObj[0].scrollHeight);
        // crrWinObj.find('.messageContent').val('');
        // $("#crrOperationWinName").val(crrWinObj.attr('id'))
        // msgStatu_timing_func($('div[data-temporary-uuid="data-temporary-uuid"]'))

        // send_message(messageContent, conversation_id, true);
        // let _datdda = {'conversation_id': conversation_id, 'text': ''}
        // websocket_emit(socket_app, 'severRelyStatu', _datdda)
        // let conversation_obj = $("#"+conversation_id)
        // if (conversation_obj.attr('data-wdState') === '1'){
        //     conversation_obj.attr('data-wdState','0');
        //     conversation_obj.attr('data-wdcount', '0');
        //     conversation_obj.find('.timingText').text('00:00:00');
        //     conversation_obj.find('.timingText').removeClass('color_red');
        //     conversation_obj.find('.CmItemnlineNumber').text('0').hide();
        // }
      }
    } else {
      if ($(".customerList").length <= 0) {
        return false;
      }
      let conversation_id = msg.conversation_id;
      let result_ls = ChackWinConversationId(conversation_id);
      const crrWinObj = result_ls[0];
      const crrIdwinSatte = result_ls[1];
      if (crrIdwinSatte) {
        const chatContentObj = crrWinObj.find(".chatContent");
        let newHtml = "";
        if (msg.content_type === "text") {
          newHtml +=
            '<div class="chat-block chatL">' +
            '<div class="inside">' +
            '<div class="userImage">' +
            '<span class="iconfont icon-windows-fill" style="font-size: 23px;"></span>' +
            "</div>" +
            '<div class="chat-name">' +
            msg.customer_name +
            '<span class="time">' +
            getShiQuTime(msg.create_time) +
            "</span>" +
            "</div>" +
            '<div class="chatting-content">' +
            '<div class="conBox">' +
            msg.text;
          if (msg.translate_text) {
            newHtml +=
              '<div class="translateText">' + msg.translate_text + "</div>";
          }
          newHtml += "</div>";
          if (msg.translate_state && !msg.translate_text) {
            newHtml +=
              '<span class="translateBtn" onclick="translateText_func($(this),\'' +
              msg.content_id +
              '\')"><i class="iconfont icon-fanyi3"></i></span>';
          }
          newHtml += "</div></div></div>";
        } else if (msg.content_type === "picture") {
          newHtml +=
            '<div class="chat-block chatL">' +
            '<div class="inside">' +
            '<div class="userImage">' +
            '<span class="iconfont icon-windows-fill" style="font-size: 23px;"></span>' +
            "</div>" +
            '<div class="chat-name">' +
            msg.customer_name +
            '<span class="time">' +
            getShiQuTime(msg.create_time) +
            "</span>" +
            "</div>" +
            '<div class="chatting-content">' +
            '<div class="conBox contentImage">' +
            '<a href="' +
            msg.file_path +
            '">' +
            '<img src="' +
            msg.file_path +
            '" alt="" style="width: 100%; display: inline-block;">' +
            "</a></div></div></div></div>";
        }
        chatContentObj.append(newHtml);
        baguetteBox.run(".chatContent");
        chatContentObj.scrollTop(chatContentObj[0].scrollHeight);
        websocket_emit(socket_app, "chatMessageReadState", {
          content_id: msg.content_id,
        });
      }
    }
  }

  // 接w收会话列表
  function socket_chatConversationList(msg) {
    // data-wdState： 0(没有未读的),1(有未读的)
    if (msg.code !== 200) {
      return;
    }
    let result_Data = msg.data;
    let totalWdNumber_obj = $("#totalWdNumber");
    if (result_Data.totalWdNumber > 0) {
      totalWdNumber_obj.show();
      totalWdNumber_obj.text(result_Data.totalWdNumber);
    } else {
      totalWdNumber_obj.hide();
      totalWdNumber_obj.text("0");
    }
    if (result_Data.datas.length > 0) {
      $(".normalTab").find(".customerItem").remove();
      $.each(result_Data.datas, function (i, item) {
        let html =
          '<div class="customerItem" id="' +
          item.uuid +
          '" style="display: flex; justify-content: space-between; align-items: center;"' +
          " onclick=\"getConversationInfo($('#chatWindowOne'),'" +
          item.uuid +
          "', $(this))\"" +
          ' data-wdCount="' +
          item.wdCount +
          '" ';
        if (item.wdCount > 0 || item.djs_statu) {
          html += ' data-wdState="1" ' + ">";
        } else {
          html += ' data-wdState="0" ' + ">";
        }
        html +=
          '<div style="width: 52px; position: relative; box-sizing: border-box;">';
        if (item.wdCount > 0) {
          html +=
            '<span class="CmItemnlineNumber" style="display: inline-block;">' +
            item.wdCount +
            "</span>";
        } else {
          html += '<span class="CmItemnlineNumber">0</span>';
        }

        if (item.client_type === "pc") {
          html +=
            '<img src="/assets/chat/images/computer.png" alt="" style="width: 35px; height: 35px; position: relative;">';
        } else {
          html +=
            '<img src="/public/chat/images/phone.png" alt="" style="width: 35px; height: 35px; position: relative;">';
        }
        html +=
          '<span style="width: 13px;height: 13px;background: #fff;border-radius: 50%; position: absolute; overflow: hidden;  display: flex; justify-content: center; align-items: center; z-index: 9; bottom: 0; right: 13px;">';
        if (item.browser_type === "chrome") {
          html +=
            '<img src="/assets/chat/images/guge.png" alt="" aria-label="" style="width: 12px; height: 12px; border-radius: 50%; margin: auto;">';
        } else if (item.browser_type === "firefox") {
          html +=
            '<img src="/assets/chat/images/firefox.png" alt="" aria-label="" style="width: 12px; height: 12px; border-radius: 50%; margin: auto;">';
        } else if (item.browser_type === "safari") {
          html +=
            '<img src="/assets/chat/images/Safari.png" alt="" aria-label="" style="width: 12px; height: 12px; border-radius: 50%; margin: auto;">';
        }

        html += "</span></div>";
        html +=
          '<div class="" style="position: relative; overflow: hidden; box-sizing: border-box; width: calc(100% - 50px);">';
        html +=
          '<div style="display: flex;line-height: 15px;margin-bottom: 3px;justify-content: center;align-items: center;">';
        html +=
          '<span style="font-size: 12px;margin-right: 8px;width: 100%;white-space: nowrap;overflow: hidden;text-overflow: ellipsis;" class="customerName">' +
          item.customer_name +
          '<span class="iconfont icon-zhiding" style="margin-left: 5px; font-size: 13px; display: none;"></span></span>';
        if (item.is_transfer) {
          html += '<div style="width: 70%;text-align: right;">';
          html +=
            '<span style=" background-image: linear-gradient(-51deg,#09acc9 0%, #57d9ce 100%), linear-gradient(#bb2424, #bb2424); padding: 1px 6px;max-width: 40%;height: 15px;color: #fff;line-height: 15px;min-width: 40px;border-radius: 3px; font-size: 10px !important; text-align: center;display: inline-block;">转接</span>&ensp;';
          html +=
            '<span style=" background-image: linear-gradient(-51deg,#09acc9 0%, #57d9ce 100%), linear-gradient(#bb2424, #bb2424); padding: 1px 6px;max-width: 40%;height: 15px;color: #fff;line-height: 15px;min-width: 40px;border-radius: 3px; font-size: 10px !important; text-align: center;display: inline-block;">' +
            item.site_name +
            "</span>";
          html += "</div>";
        } else {
          html += '<div style="width: 70%;text-align: right;">';
          html +=
            '<span style=" background-image: linear-gradient(-51deg,#09acc9 0%, #57d9ce 100%), linear-gradient(#bb2424, #bb2424); padding: 1px 6px;max-width: 40%;height: 15px;color: #fff;line-height: 15px;min-width: 40px;border-radius: 3px; font-size: 10px !important; text-align: center;display: inline-block;">' +
            item.site_name +
            "</span>";
          html += "</div>";
        }
        html +=
          '</div><div style="display: block; font-size: 12px; overflow: hidden; position: relative;">';
        if (item.statu === ConversationStatu.waiting) {
          html +=
            '<span style="float: left;" class="ConversationStateTime">离线时间：' +
            item.disconnect_tiem +
            "</span>";
        } else if (item.statu === ConversationStatu.normal) {
          html +=
            '<span style="float: left;" class="ConversationStateTime">进程时间：' +
            item.start_time +
            "</span>";
        }
        html += '<span style="float: right;">等待时间：<span class="timingText">00:00:00</span></span>';
        html += "</div></div></div>";
        if ($("#" + item.uuid).length <= 0) {
          $(".normalTab").append(html);
          if (item.wdCount > 0 || item.djs_statu) {
            timing_func(
              $("#" + item.uuid),
              item.djs_h,
              item.djs_m,
              item.djs_s,
              item.uuid,
              item.is_automatic
            );
          }
          if (item.statu === ConversationStatu.waiting) {
            console.log("here1");
            offline_timing_func(item.uuid, item.djs_m, item.djs_s);
          }
        }
      });
      $(".nor_onCustomer").hide();
      $("#contLoading").css("display", "none");
    } else {
      $("#contLoading").css("display", "none");
      $(".nor_onCustomer").show();
    }
  }

  // 接收会话信息
  function socket_chatConversationInfo(msg) {
    let currentChatWindowsOne = false;
    let currentChatWindowsTwo = false;
    let currentChatWindowsThree = false;
    let chatWindowOne_show = false;
    let chatWindowTwo_show = false;
    let chatWindowThree_show = false;
    let conversation_id = msg.conversation_id;

    const timingTextObj = $("#" + conversation_id).find(".timingText");
    if (timingTextObj.hasClass("color_red")) {
      timingTextObj.removeClass("color_red");
    }

    let result_ls = ChackWinConversationId(conversation_id);
    const currentChatWindows = result_ls[0];
    const crrIdwinState = result_ls[1];
    let winTotal = 0;
    if ($("#chatWindowOne").css("display") !== "none") {
      chatWindowOne_show = true;
      winTotal += 1;
    }
    if ($("#chatWindowTwo").css("display") !== "none") {
      chatWindowTwo_show = true;
      winTotal += 1;
    }
    if ($("#chatWindowThree").css("display") !== "none") {
      chatWindowThree_show = true;
      winTotal += 1;
    }

    if ($("#chatWindowOneConversationId").val() === conversation_id) {
      currentChatWindowsOne = true;
    } else if ($("#chatWindowTwoConversationId").val() === conversation_id) {
      currentChatWindowsTwo = true;
    } else if ($("#chatWindowThreeConversationId").val() === conversation_id) {
      currentChatWindowsThree = true;
    }

    if (msg.client_type === "pc") {
      currentChatWindows
        .find(".onlineState img")
        .attr("src", "/assets/chat/images/computer.png");
    } else {
      currentChatWindows
        .find(".onlineState img")
        .attr("src", "/public/chat/images/phone.png");
    }

    if (msg.conversation_statu === "waiting") {
      currentChatWindows.find(".userportrait").show();
    } else {
      currentChatWindows.find(".userportrait").hide();
    }

    if (msg.customer_data.username) {
      currentChatWindows
        .find(".crr_customer_name")
        .text(msg.customer_data.username);
    } else if (msg.customer_name) {
      currentChatWindows.find(".crr_customer_name").text(msg.customer_name);
    }

    if (currentChatWindowsOne) {
      setInfoCard(msg);
    }

    currentChatWindows.find(".chatLoading").hide();
    currentChatWindows.find(".chatContent").find(".chat-block").remove();
    if (msg.info_data.length > 0) {
      let infoHtml = "";
      $.each(msg.info_data, function (i, item) {
        let ctt_customer_name = "";
        let service_data = item.service_data;
        if (msg.customer_data.username) {
          ctt_customer_name = msg.customer_data.username;
        } else {
          ctt_customer_name = msg.customer_name;
        }
        if (item.is_service) {
          if (item.content_type === "text") {
            infoHtml +=
              '<div class="chat-block chatR" data-timeStamp="' +
              item.timeStamp +
              '" data-uuid="' +
              item.uuid +
              '">' +
              '<div class="inside">' +
              '<img src="' +
              service_data.portrait +
              '" alt="" class="userImage">' +
              '<div class="chat-name">' +
              service_data.service_name +
              '<span class="time">' +
              getShiQuTime(item.create_time) +
              "</span>" +
              "</div>" +
              '<div class="chatting-content">';
            if (item.customer_reading_state) {
              infoHtml +=
                '<span class="msgStatu"><i class="iconfont icon-round_check"></i></span>';
            } else {
              infoHtml +=
                '<span class="msgStatu"><i class="iconfont icon-round"></i></span>';
            }
            infoHtml +=
              '<div class="conBox">' +
              item.text +
              "</div>" +
              "</div></div></div>";
          } else if (item.content_type === "picture") {
            infoHtml +=
              '<div class="chat-block chatR" data-uuid="' +
              item.uuid +
              '">' +
              '<div class="inside">' +
              '<img src="' +
              service_data.portrait +
              '" alt="" class="userImage">' +
              '<div class="chat-name">' +
              service_data.service_name +
              '<span class="time">' +
              getShiQuTime(item.create_time) +
              "</span>" +
              "</div>" +
              '<div class="chatting-content">';
            if (item.customer_reading_state) {
              infoHtml +=
                '<span class="msgStatu"><i class="iconfont icon-round_check"></i></span>';
            } else {
              infoHtml +=
                '<span class="msgStatu"><i class="iconfont icon-round"></i></span>';
            }
            infoHtml +=
              '<div class="conBox contentImage">' +
              '<a href="' +
              item.file_path +
              '">' +
              '<img src="' +
              item.file_path +
              '" alt="" style="width: 100%; display: inline-block;">' +
              "</a>" +
              "</div>" +
              "</div></div></div>";
          } else if (item.content_type === ContentTypes.FILE) {
            infoHtml +=
              '<div class="chat-block chatR" data-uuid="' +
              item.uuid +
              '">' +
              '<div class="inside">' +
              '<img src="' +
              service_data.portrait +
              '" alt="" class="userImage">' +
              '<div class="chat-name">' +
              service_data.service_name +
              '<span class="time">' +
              getShiQuTime(item.create_time) +
              "</span>" +
              "</div>" +
              '<div class="chatting-content">';
            if (item.customer_reading_state) {
              infoHtml +=
                '<span class="msgStatu"><i class="iconfont icon-round_check"></i></span>';
            } else {
              infoHtml +=
                '<span class="msgStatu"><i class="iconfont icon-round"></i></span>';
            }
            infoHtml +=
              '<div class="conBox">' +
              '<div class="conFile">' +
              '<div style="position: relative; box-sizing: border-box; display: flex; align-items: center;">' +
              '<i class="iconfont icon-file-word-fill" style="font-size: 49px; color: #6c757d;"></i>' +
              "</div>" +
              '<div style="position: relative;box-sizing: border-box;display: flex;flex-direction: column;line-height: 20px;font-size: 12px;color: #545b62;margin-left: 15px;min-width: 120px;text-align: left;">' +
              '<span style="max-width: 180px; white-space: nowrap;overflow: hidden;text-overflow: ellipsis; position: relative; display: block;">' +
              item.filename +
              "</span>" +
              "<span>" +
              item.file_size +
              "KB</span>" +
              "</div>" +
              '<div class="xiaZai">' +
              "<a onclick=\"download_func('" +
              item.file_path +
              "')\">" +
              '<i class="iconfont icon-yunxiazai1"></i>' +
              "</a></div></div>" +
              "</div></div></div></div>";
          }
        }
        if (item.is_customer) {
          if (item.content_type === "text") {
            infoHtml +=
              '<div class="chat-block chatL">' +
              '<div class="inside">' +
              '<div class="userImage">' +
              '<span class="iconfont icon-windows-fill" style="font-size: 23px;"></span>' +
              "</div>" +
              '<div class="chat-name">' +
              ctt_customer_name +
              '<span class="time">' +
              getShiQuTime(item.create_time) +
              "</span>" +
              "</div>" +
              '<div class="chatting-content">' +
              '<div class="conBox">' +
              item.text;
            if (item.translate_text) {
              infoHtml +=
                '<div class="translateText">' + item.translate_text + "</div>";
            }
            infoHtml += "</div>";
            if (msg.translate_state && !item.translate_text) {
              infoHtml +=
                '<span class="translateBtn" onclick="translateText_func($(this),\'' +
                item.uuid +
                '\')"><i class="iconfont icon-fanyi3"></i></span>';
            }
            infoHtml += "</div></div></div>";
          } else if (item.content_type === "picture") {
            infoHtml +=
              '<div class="chat-block chatL">' +
              '<div class="inside">' +
              '<div class="userImage">' +
              '<span class="iconfont icon-windows-fill" style="font-size: 23px;"></span>' +
              "</div>" +
              '<div class="chat-name">' +
              ctt_customer_name +
              '<span class="time">' +
              getShiQuTime(item.create_time) +
              "</span>" +
              "</div>" +
              '<div class="chatting-content">' +
              '<div class="conBox contentImage">' +
              '<a href="' +
              item.file_path +
              '">' +
              '<img src="' +
              item.file_path +
              '" alt="" style="width: 100%; display: inline-block;">' +
              "</a></div></div></div></div>";
          }
          else if (item.content_type === "video") {
            infoHtml +=
              "" +
              '                    <div class="chat-block chatL">\n' +
              '                        <div class="inside">\n' +
              '                            <div class="userImage">\n' +
              '                                <span class="iconfont icon-windows-fill" style="font-size: 23px;"></span>\n' +
              "                            </div>\n" +
              '<div class="chat-name">' +
              ctt_customer_name +
              '<span class="time">' +
              getShiQuTime(item.create_time) +
              "</span>" +
              "</div>" +
              '                            <div class="chatting-content">\n' +
              '                                       <video width="400" height="auto" controls> ' +
              "<source src='" +
              item.file_path +
              '\' type="video/mp4"/>' +
              "</video>" +
              "                            </div>\n" +
              "                        </div>\n" +
              "                    </div>";
          }
        }
      });
      const chatContentObj = currentChatWindows.find(".chatContent");
      chatContentObj.append(infoHtml);
      let tt = setTimeout(function () {
        chatContentObj.scrollTop(chatContentObj[0].scrollHeight);
      }, 500);
      baguetteBox.run(".chatContent");
    }

    if (!currentChatWindowsOne) {
      $(".infoBox").hide(0);
    } else {
      if (
        !currentChatWindowsTwo &&
        !currentChatWindowsThree &&
        !chatWindowTwo_show &&
        !chatWindowThree_show
      ) {
        $(".infoBox").show(0);
      }
    }

    if (currentChatWindows.css("display") === "none") {
      if (winTotal === 0) {
        $(".infoBox").show();
        $(".chatManageBox").css("width", "calc(100% - 490px)");
        currentChatWindows.css("left", "0px");
      }
      if (winTotal === 1) {
        $(".infoBox").hide();
        $(".chatManageBox").css("width", "calc((100% - 15px) / 2)");
        if (chatWindowOne_show) {
          if (currentChatWindowsTwo) {
            $("#chatWindowTwo").css("left", "calc((100% - 15px) / 2 + 10px)");
          }
          if (currentChatWindowsThree) {
            $("#chatWindowThree").css("left", "calc((100% - 15px) / 2 + 10px)");
          }
        }
        if (chatWindowTwo_show) {
          if (currentChatWindowsOne) {
            $("#chatWindowTwo").css("left", "calc((100% - 15px) / 2 + 10px)");
          }
          if (currentChatWindowsThree) {
            $("#chatWindowThree").css("left", "calc((100% - 15px) / 2 + 10px)");
          }
        }
        if (chatWindowThree_show) {
          if (currentChatWindowsOne) {
            $("#chatWindowThree").css("left", "calc((100% - 15px) / 2 + 10px)");
          }
          if (currentChatWindowsTwo) {
            $("#chatWindowThree").css("left", "calc((100% - 15px) / 2 + 10px)");
          }
        }
      }
      if (winTotal === 2) {
        $(".chatManageBox").css("width", "calc((100% - 25px) / 3)");
        $("#chatWindowTwo").css("left", "calc((100% - 25px) / 3 + 10px)");
        $("#chatWindowThree").css("left", "calc((100% - 25px) / 3 * 2 + 20px)");
      }
      currentChatWindows.show(0);
    }
    currentChatWindows.find(".uploadImage").attr("accept", msg.kz_image_types);
    currentChatWindows.find(".uploadfile").attr("accept", msg.kz_file_types);
  }

  // 客户在线实时统计
  function socket_chatCtnOnlineCount(msg) {
    if (msg.crr_service_id === service_id) {
      $(".onlineTotalCount").find("span").text(msg.onlineTotal);
      $(".crrOnlineCount").find("span").text(msg.onlinePresent);
    }
    let conversation_id = msg.conversation_id;
    const ConversationObj = $("#" + conversation_id);
    if (ConversationObj.length > 0) {
      if (msg.connectionState && conversation_id) {
        let result_ls = ChackWinConversationId(conversation_id);
        const crrWinObj = result_ls[0];
        const crrIdwinSatte = result_ls[1];
        if (crrIdwinSatte) {
          if (msg.connectionState === "0") {
            ConversationObj.attr("data-connectionState", "0");
            ConversationObj.find(".ConversationStateTime").text(
              "离线时间：" + msg.disconnect_tiem
            );
            crrWinObj.find(".userportrait").show();
            console.log("here2");
            offline_timing_func(msg.conversation_id);
          } else if (msg.connectionState === "1") {
            ConversationObj.attr("data-connectionState", "1");
            ConversationObj.find(".ConversationStateTime").text(
              "进程时间：" + msg.start_time
            );
            crrWinObj.find(".userportrait").hide();
          }
        } 
        else {
          if (msg.connectionState === "0") {
            ConversationObj.attr("data-connectionState", "0");
            ConversationObj.find(".ConversationStateTime").text(
              "离线时间：" + msg.disconnect_tiem
            );
            if (parseInt($("#" + msg.conversation_id).attr("data-wdCount")) <= 0) {
              console.log("here3");
              offline_timing_func(msg.conversation_id);
            }
          } else if (msg.connectionState === "1") {
            ConversationObj.attr("data-connectionState", "1");
            ConversationObj.find(".ConversationStateTime").text(
              "进程时间：" + msg.start_time
            );
          }
        }
      }
    }
  }

  // 接收新增用户
  function socket_chatNewConversation(msg) {
    if ($("#" + msg.uuid).length > 0) {
      return;
    }

    let normalTabObj = $(".normalTab");
    let html =
      '<div class="customerItem" id="' +
      msg.uuid +
      '" style="display: flex; justify-content: space-between; align-items: center;"' +
      " onclick=\"getConversationInfo($('#chatWindowOne'),'" +
      msg.uuid +
      "', $(this))\"" +
      ' data-wdCount="' +
      msg.wdCount +
      '" ';
    if (msg.wdCount > 0) {
      html += ' data-wdState="1" ' + ">";
    } else {
      html += ' data-wdState="0" ' + ">";
    }
    html +=
      '<div style="width: 52px; position: relative; box-sizing: border-box;">';

    if (msg.wdCount > 0) {
      html +=
        '<span class="CmItemnlineNumber" style="display: inline-block;">' +
        msg.wdCount +
        "</span>";
    } else {
      html += '<span class="CmItemnlineNumber">0</span>';
    }

    if (msg.client_type === "pc") {
      html +=
        '<img src="/assets/chat/images/computer.png" alt="" style="width: 35px; height: 35px; position: relative;">';
    } else {
      html +=
        '<img src="/public/chat/images/phone.png" alt="" style="width: 35px; height: 35px; position: relative;">';
    }
    html +=
      '<span style="width: 13px;height: 13px;background: #fff;border-radius: 50%; position: absolute; overflow: hidden;  display: flex; justify-content: center; align-items: center; z-index: 9; bottom: 0; right: 13px;">';
    if (msg.browser_type === "chrome") {
      html +=
        '<img src="/assets/chat/images/guge.png" alt="" aria-label="" style="width: 12px; height: 12px; border-radius: 50%; margin: auto;">';
    } else if (msg.browser_type === "firefox") {
      html +=
        '<img src="/assets/chat/images/firefox.png" alt="" aria-label="" style="width: 12px; height: 12px; border-radius: 50%; margin: auto;">';
    } else if (msg.browser_type === "safari") {
      html +=
        '<img src="/assets/chat/images/Safari.png" alt="" aria-label="" style="width: 12px; height: 12px; border-radius: 50%; margin: auto;">';
    }

    html += "</span></div>";
    html +=
      '<div class="" style="position: relative; overflow: hidden; box-sizing: border-box; width: calc(100% - 50px);">';
    html +=
      '<div style="display: flex;line-height: 15px;margin-bottom: 3px;justify-content: center;align-items: center;">';
    html +=
      '<span style="font-size: 12px;margin-right: 8px;width: 100%;white-space: nowrap;overflow: hidden;text-overflow: ellipsis;" class="customerName">' +
      msg.customer_name +
      '<span class="iconfont icon-zhiding" style="margin-left: 5px; font-size: 13px; display: none;"></span></span>';

    if (msg.is_transfer) {
      html += '<div style="width: 70%;text-align: right;">';
      html +=
        '<span style=" background-image: linear-gradient(-51deg,#09acc9 0%, #57d9ce 100%), linear-gradient(#bb2424, #bb2424); padding: 1px 6px;max-width: 40%;height: 15px;color: #fff;line-height: 15px;min-width: 40px;border-radius: 3px; font-size: 10px !important; text-align: center;display: inline-block;">转接</span>&ensp;';
      html +=
        '<span style=" background-image: linear-gradient(-51deg,#09acc9 0%, #57d9ce 100%), linear-gradient(#bb2424, #bb2424); padding: 1px 6px;max-width: 40%;height: 15px;color: #fff;line-height: 15px;min-width: 40px;border-radius: 3px; font-size: 10px !important; text-align: center;display: inline-block;">' +
        msg.site_name +
        "</span>";
      html += "</div>";
    } else {
      html += '<div style="width: 70%;text-align: right;">';
      html +=
        '<span style=" background-image: linear-gradient(-51deg,#09acc9 0%, #57d9ce 100%), linear-gradient(#bb2424, #bb2424); padding: 1px 6px;max-width: 40%;height: 15px;color: #fff;line-height: 15px;min-width: 40px;border-radius: 3px; font-size: 10px !important; text-align: center;display: inline-block;">' +
        msg.site_name +
        "</span>";
      html += "</div>";
    }
    html +=
      '</div><div style="display: block; font-size: 12px; overflow: hidden; position: relative;">';
    html +=
      '<span style="float: left;" class="ConversationStateTime">进程时间：' +
      msg.start_time +
      "</span>";
    html +=
      '<span style="float: right;">等待时间：<span class="timingText">00:00:00</span></span>';
    html += "</div></div></div>";

    if (msg.service_id === service_id && normalTabObj.length > 0) {
      if (beep_switch) {
        let mp3ll = new Audio("/static/common/audio/lingsheng.mp3"); // 创建音频对象
        mp3ll.loop = false;
        mp3ll.play(); // 播放
      }

      if (normalTabObj.find(".customerItem").length <= 0) {
        $(".nor_onCustomer").hide();
      }
      if ($("#" + msg.uuid).length <= 0) {
        $(".selectMyTs").after(html);
      }
    }
  }

  // 接口客户监控信息
  function socket_ChatServerSideMessage(msg) {
    let text = $.trim(msg.text);
    let conversation_id = msg.conversation_id;

    let result_ls = ChackWinConversationId(conversation_id);
    const crrWinObj = result_ls[0];
    const crrIdwinSatte = result_ls[1];
    if (!conversation_id) {
      return;
    }
    if (crrIdwinSatte) {
      let monitorChat_obj = crrWinObj.find(".monitorChat");
      const chatContetntObj = crrWinObj.find(".chatContent");
      if (!text || text === "") {
        let dd = crrWinObj.find(".messageTop").innerHeight() - 58;
        chatContetntObj.css("height", dd + "px");
        return monitorChat_obj.hide();
      }
      monitorChat_obj.text(text).show();
      let mh = monitorChat_obj.innerHeight();
      let dd = crrWinObj.find(".messageTop").innerHeight() - 58 - mh;
      chatContetntObj.css("height", dd + "px");
    }
  }

  // 图片上传反馈
  function socket_ServerSideUploadFeedback(msg) {
    let file_path = msg.file_path;
    let create_time = msg.create_time;
    let content_type = msg.content_type;
    if (!file_path || !content_type) {
      return;
    }

    const crrStamp = parseInt(Date.now() / 1000);

    let chtHtml = "";
    chtHtml +=
      '<div class="chat-block chatR" data-timeStamp="' +
      crrStamp +
      '" data-uuid="' +
      msg.data_uuid +
      '">' +
      '<div class="inside">' +
      '<img src="' +
      service_portrait +
      '" alt="" class="userImage">' +
      '<div class="chat-name">' +
      service_name +
      '<span class="time">' +
      getShiQuTime(create_time) +
      "</span>" +
      "</div>" +
      '<div class="chatting-content">' +
      '<span class="msgStatu"><i class="iconfont icon-round"></i></span>' +
      '<div class="conBox contentImage">' +
      '<a href="' +
      file_path +
      '" target="_blank">' +
      '<img src="' +
      file_path +
      '" alt="" style="width: 100%; display: inline-block;">' +
      "</a>" +
      "</div>" +
      '<div class="retract_message">撤回消息</div>' +
      "</div></div></div>";

    let crrWinObj = $("#" + $("#crrOperationWinName").val());
    const chatContentObj = crrWinObj.find(".chatContent");
    chatContentObj.append(chtHtml);
    crrWinObj.find(".monitorChat").hide();
    baguetteBox.run(".chatContent");
    let tt = setTimeout(function () {
      chatContentObj.scrollTop(chatContentObj[0].scrollHeight);
    }, 500);

    let conversation_id = crrWinObj.find(".chatWinConversationId").val();
    let conversation_obj = $("#" + conversation_id);
    if (conversation_obj.attr("data-wdState") === "1") {
      conversation_obj.attr("data-wdState", "0");
      conversation_obj.attr("data-wdcount", "0");
      conversation_obj.find(".timingText").text("00:00:00");
      conversation_obj.find(".timingText").removeClass("color_red");
      conversation_obj.find(".CmItemnlineNumber").text("0").hide();
    }
  }

  // 接收结束聊天
  function socket_chatFinishConversation(msg) {
    let conversation_id = msg.conversation_id;
    let crr_service_sid = msg.crr_service_sid;
    $("#" + conversation_id).remove();

    let result_ls = ChackWinConversationId(conversation_id);
    const crrWinObj = result_ls[0];
    const crrIdwinSatte = result_ls[1];

    if (crr_service_sid === service_id) {
      if (crrIdwinSatte) {
        winAutomationFunc(crrWinObj);
        crrWinObj.find(".chatWinConversationId").val("");
        crrWinObj.find(".chatContent").find(".chat-block").remove();
        xtalert.alertInfo("当前聊天已结束，请到结束列表查看！");
      }

      if ($(".normalTab").find(".customerItem").length <= 0) {
        $(".nor_onCustomer").show();
      }
    }
  }

  // 结束列表
  function socket_serviceFinishList(msg) {
    if (msg.code !== 200) {
      return;
    }
    let result_Datas = msg.data;
    $("#hhListLoading").css("display", "none");
    if (result_Datas.length > 0) {
      $.each(result_Datas, function (i, item) {
        let html =
          '<div class="customerItem" id="' +
          item.uuid +
          '" style="display: flex; justify-content: space-between; align-items: center;"' +
          " onclick=\"getConversationInfo($('#chatWindowOne'),'" +
          item.uuid +
          "', $(this), true)\"" +
          ' data-finish="1">';
        html +=
          '<div style="width: 52px; position: relative; box-sizing: border-box;">';

        if (item.client_type == "pc") {
          html +=
            '<img src="/assets/chat/images/computer.png" alt="" style="width: 35px; height: 35px; position: relative;">';
        } else {
          html +=
            '<img src="/public/chat/images/phone.png" alt="" style="width: 35px; height: 35px; position: relative;">';
        }
        html +=
          '<span style="width: 13px;height: 13px;background: #fff;border-radius: 50%; position: absolute; overflow: hidden;  display: flex; justify-content: center; align-items: center; z-index: 9; bottom: 0; right: 13px;">';
        if (item.browser_type == "chrome") {
          html +=
            '<img src="/assets/chat/images/guge.png" alt="" aria-label="" style="width: 12px; height: 12px; border-radius: 50%; margin: auto;">';
        } else if (item.browser_type == "firefox") {
          html +=
            '<img src="/assets/chat/images/firefox.png" alt="" aria-label="" style="width: 12px; height: 12px; border-radius: 50%; margin: auto;">';
        } else if (item.browser_type == "safari") {
          html +=
            '<img src="/assets/chat/images/Safari.png" alt="" aria-label="" style="width: 12px; height: 12px; border-radius: 50%; margin: auto;">';
        }

        html += "</span></div>";
        html +=
          '<div class="" style="position: relative; overflow: hidden; box-sizing: border-box; width: calc(100% - 50px);">';
        html +=
          '<div style="line-height: 15px; margin-bottom: 3px; display: flex; justify-content: space-between;">';
        html +=
          '<span style="font-size: 12px; margin-right: 8px;" class="customerName">' +
          item.customer_name +
          "</span>";
        html +=
          '<span style=" background-image: linear-gradient(-51deg,#09acc9 0%, #57d9ce 100%), linear-gradient(#bb2424, #bb2424); padding: 1px 6px;max-width: 40%;height: 15px;color: #fff;line-height: 15px;min-width: 40px;border-radius: 3px; font-size: 10px !important; text-align: center;display: inline-block;">' +
          item.site_name +
          "</span>";
        html +=
          '</div><div style="display: block; font-size: 12px; overflow: hidden; position: relative;">';
        html +=
          '<span style="float: left;">进程时间：' + item.start_time + "</span>";
        html +=
          '<span style="float: right;">离线时间：' + item.end_time + "</span>";
        html += "</div></div></div>";
        $(".finishList").append(html);
      });
    } else {
      $(".fsh_onCustomer").show();
    }
  }

  // 服务器反馈
  function socket_serverFeedback(msg) {
    const feedback_data = msg.data;

    if (msg.code !== 200) {
      return false;
    }

    // 文本消息反馈处理
    if (
      feedback_data.type === "text_message_feedback" ||
      feedback_data.type === "upload_file_feedback"
    ) {
      const temporary_data_id = feedback_data.temporary_data_id;
      let crr_message_html = $(
        "div[data-temporary-uuid='" + temporary_data_id + "']"
      );
      if (!crr_message_html) {
        return;
      }
      crr_message_html.attr("data-uuid", feedback_data.data_id);

      crr_message_html.attr("data-msgStatu", "2");
      crr_message_html
        .find(".msgStatu")
        .find(".iconfont")
        .removeClass("icon-jiazai2")
        .addClass("icon-round");
    } else if (feedback_data.type === "retractMessage") {
      const message_data_uuid = feedback_data.data_uuid;
      const messageObj = $("div[data-uuid='" + message_data_uuid + "']");
      if (!messageObj) {
        return;
      }
      messageObj.css("padding-bottom", "20px");
      let html =
        '<div style="display: block; text-align: center; font-size: 12px; color: rgb(153, 153, 153); margin-top: 10px;">您撤回了一条消息</div>';
      messageObj.empty().append(html);
    } else if (feedback_data.type === "forceOutLogin") {
      if (feedback_data.state) {
        return xtalert.alertSuccessToast(feedback_data.msg);
      } else {
        return xtalert.alertError(feedback_data.msg);
      }
    } else if (feedback_data.type === "transferConversation") {
      if (feedback_data.statu) {
        let result_ls = ChackWinConversationId(feedback_data.conversation_id);
        const crrWinObj = result_ls[0];
        const crrIdwinSatte = result_ls[1];
        if (crrIdwinSatte) {
          winAutomationFunc(crrWinObj);
          crrWinObj.hide();
          crrWinObj.find(".chat-block").remove();
          crrWinObj.find(".crr_customer_name").text("");
          crrWinObj.find(".chatWinConversationId").val("");
        }
        let conversation_obj = $("#" + feedback_data.conversation_id);
        let data_wdState = conversation_obj.attr("data-wdState");
        if (data_wdState) {
          let lowWdCount = parseInt(conversation_obj.attr("data-wdCount"));
          if (lowWdCount > 0) {
            let totalWdNumber_obj = $("#totalWdNumber");
            let low_tt = $.trim(totalWdNumber_obj.text());
            totalWdNumber_obj.text((parseInt(low_tt) - lowWdCount).toString());
            totalWdNumber_obj.show();
          }
        }
        conversation_obj.remove();
        if ($(".normalTab").find(".customerItem").length <= 0) {
          $(".nor_onCustomer").show();
        }
        return xtalert.alertSuccessToast("转接成功！");
      } else {
        return xtalert.alertError("转接失败!");
      }
    } else if (feedback_data.type === "customerWinFocus") {
      let result_ls = ChackWinConversationId(feedback_data.conversation_id);
      const crrWinObj = result_ls[0];
      const crrIdwinSatte = result_ls[1];
      if (crrWinObj && crrIdwinSatte) {
        crrWinObj.find(".chatR").each(function (index, vobj) {
          $(this)
            .find(".icon-round")
            .removeClass("icon-round")
            .addClass("icon-round_check");
        });
      }
    } else if (feedback_data.type === "update_leavingCount") {
      if (feedback_data.site_code === site_code) {
        let leavingCount = feedback_data.leavingCount;
        if (leavingCount > 0) {
          $("#leavingCount").text(leavingCount);
          $("#leavingCount").show();
        } else {
          $("#leavingCount").hide();
        }
      }
    }
  }

  // 接受查看同事客服会话列表
  function socket_serviceConversationList(msg) {
    const code = msg.code;
    const total = msg.data.total;
    const msg_datas = msg.data.datas;
    if (code !== 200) {
      return false;
    }
    $(".normalTab").find(".customerItem").remove();
    if (!msg_datas || msg_datas.length <= 0 || total <= 0) {
      $(".nor_onCustomer").show();
      $("#contLoading").css("display", "none");
      return false;
    }
    $.each(msg_datas, function (index1, v1) {
      let tdatas = v1.datas;
      if (tdatas.length > 0) {
        $.each(tdatas, function (index2, item) {
          let html =
            '<div class="customerItem" id="' +
            item.uuid +
            '" style="display: flex; justify-content: space-between; align-items: center;"' +
            " onclick=\"getConversationInfo($('#chatWindowOne'),'" +
            item.uuid +
            "', $(this))\"";
          if (item.wdCount > 0 || item.djs_statu) {
            html += ' data-wdState="1" ' + ">";
          } else {
            html += ' data-wdState="0" ' + ">";
          }
          html +=
            '<div style="width: 52px; position: relative; box-sizing: border-box;">';
          if (item.client_type == "pc") {
            html +=
              '<img src="/assets/chat/images/computer.png" alt="" style="width: 35px; height: 35px; position: relative;">';
          } else {
            html +=
              '<img src="/public/chat/images/phone.png" alt="" style="width: 35px; height: 35px; position: relative;">';
          }
          html +=
            '<span style="width: 13px;height: 13px;background: #fff;border-radius: 50%; position: absolute; overflow: hidden;  display: flex; justify-content: center; align-items: center; z-index: 9; bottom: 0; right: 13px;">';
          if (item.browser_type == "chrome") {
            html +=
              '<img src="/assets/chat/images/guge.png" alt="" aria-label="" style="width: 12px; height: 12px; border-radius: 50%; margin: auto;">';
          } else if (item.browser_type == "firefox") {
            html +=
              '<img src="/assets/chat/images/firefox.png" alt="" aria-label="" style="width: 12px; height: 12px; border-radius: 50%; margin: auto;">';
          } else if (item.browser_type == "safari") {
            html +=
              '<img src="/assets/chat/images/Safari.png" alt="" aria-label="" style="width: 12px; height: 12px; border-radius: 50%; margin: auto;">';
          }
          html += "</span></div>";
          html +=
            '<div class="" style="position: relative; overflow: hidden; box-sizing: border-box; width: calc(100% - 50px);">';
          html +=
            '<div style="display: flex;line-height: 15px;margin-bottom: 3px;justify-content: center;align-items: center;">';
          html +=
            '<span style="font-size: 12px;margin-right: 8px;width: 100%;white-space: nowrap;overflow: hidden;text-overflow: ellipsis;" class="customerName">' +
            item.customer_name +
            '<span class="iconfont icon-zhiding" style="margin-left: 5px; font-size: 13px; display: none;"></span></span>';
          html += '<div style="width: 70%;text-align: right;">';
          html +=
            '<span style=" background-image: linear-gradient(-51deg,#09acc9 0%, #57d9ce 100%), linear-gradient(#bb2424, #bb2424); padding: 1px 6px;max-width: 40%;height: 15px;color: #fff;line-height: 15px;min-width: 50px;border-radius: 3px; font-size: 10px !important; text-align: center;">' +
            item.site_name +
            "</span>";
          html += "</div>";
          html +=
            '</div><div style="display: block; font-size: 12px; overflow: hidden; position: relative;">';
          if (item.statu === ConversationStatu.waiting) {
            html +=
              '<span style="float: left;" class="ConversationStateTime">离线时间：' +
              item.disconnect_tiem +
              "</span>";
          } else if (item.statu === ConversationStatu.normal) {
            html +=
              '<span style="float: left;" class="ConversationStateTime">进程时间：' +
              item.start_time +
              "</span>";
          }
          html +=
            '<span style="float: right; color: #57d9ce;">' +
            v1.uname +
            ': <i class="iconfont icon-kefufill"></i></span>';
          html += "</div></div></div>";
          $(".nor_onCustomer").hide();
          $(".normalTab").append(html);
        });
      }
    });
    $(".nor_onCustomer").hide();
    $("#contLoading").css("display", "none");
  }

  // 接收同事客服统计
  function socket_ServerReceiveConversationTotal(msg) {
    if (msg.code !== 200) {
      return false;
    }
    let result_data = msg.data;
    if (result_data.length <= 0) {
      $(".popoverCont .no-Cer").show();
      return false;
    }
    $(".selectTsList").find(".popoItme").remove();
    let html = "";
    $.each(result_data, function (index, v) {
      html +=
        '                                    <div class="popoItme" ' +
        ' data-serviceid="' +
        v.u_id +
        '"' +
        ">\n" +
        "                                        <div>\n" +
        '                                            <img src="' +
        v.portrait +
        '" alt="">\n' +
        '                                            <span class="serviceName">' +
        v.uname +
        "</span>\n" +
        "                                        </div>\n" +
        "                                        <div>\n" +
        '                                            <span class="badge badge-pill badge-danger">' +
        v.total +
        "</span>\n" +
        "                                        </div>\n" +
        "                                    </div>";
    });
    $(".selectTsList .popoverCont").append(html);
    $(".selectTsList .no-Cer").hide();
  }

  // 接收同事客服发送的信息
  function socket_receiveTsConversationMsg(msg) {
    if (msg.code !== 200) {
      return false;
    }
    let msg_data = msg.data;
    let ccr_service_id = msg_data.service_id;
    if (ccr_service_id === service_id) {
      return;
    }

    let item = msg_data.data;
    let service_data = msg_data.service_data;
    let conversation_id = msg_data.conversation_id;
    let result_ls = ChackWinConversationId(conversation_id);
    const crrWinObj = result_ls[0];
    const crrIdwinSatte = result_ls[1];
    if (!crrIdwinSatte) {
      return false;
    }

    let infoHtml = "";
    if (item.content_type === "text") {
      infoHtml +=
        '<div class="chat-block chatR" data-timeStamp="' +
        item.timeStamp +
        '" data-uuid="' +
        item.uuid +
        '">' +
        '<div class="inside">' +
        '<img src="' +
        service_data.portrait +
        '" alt="" class="userImage">' +
        '<div class="chat-name">' +
        service_data.service_name +
        '<span class="time">' +
        getShiQuTime(item.create_time) +
        "</span>" +
        "</div>" +
        '<div class="chatting-content">' +
        '<span class="msgStatu"><i class="iconfont icon-round"></i></span>' +
        '<div class="conBox">' +
        item.text +
        "</div>" +
        "</div></div></div>";
    } else if (item.content_type === "picture") {
      infoHtml +=
        '<div class="chat-block chatR" data-uuid="' +
        item.uuid +
        '">' +
        '<div class="inside">' +
        '<img src="' +
        service_data.portrait +
        '" alt="" class="userImage">' +
        '<div class="chat-name">' +
        service_data.service_name +
        '<span class="time">' +
        getShiQuTime(item.create_time) +
        "</span>" +
        "</div>" +
        '<div class="chatting-content">' +
        '<span class="msgStatu"><i class="iconfont icon-round"></i></span>' +
        '<div class="conBox contentImage">' +
        '<a href="' +
        item.file_path +
        '">' +
        '<img src="' +
        item.file_path +
        '" alt="" style="width: 100%; display: inline-block;">' +
        "</a>" +
        "</div>" +
        "</div></div></div>";
    } else {
      infoHtml +=
        '<div class="chat-block chatR" data-uuid="' +
        item.uuid +
        '">' +
        '<div class="inside">' +
        '<img src="' +
        service_data.portrait +
        '" alt="" class="userImage">' +
        '<div class="chat-name">' +
        service_data.service_name +
        '<span class="time">' +
        getShiQuTime(item.create_time) +
        "</span>" +
        "</div>" +
        '<div class="chatting-content">' +
        '<span class="msgStatu"><i class="iconfont icon-round"></i></span>' +
        '<div class="conBox">' +
        '<div class="conFile">' +
        '<div style="position: relative; box-sizing: border-box; display: flex; align-items: center;">' +
        '<i class="iconfont icon-file-word-fill" style="font-size: 49px; color: #6c757d;"></i>' +
        "</div>" +
        '<div style="position: relative;box-sizing: border-box;display: flex;flex-direction: column;line-height: 20px;font-size: 12px;color: #545b62;margin-left: 15px;min-width: 120px;text-align: left;">' +
        '<span style="max-width: 180px; white-space: nowrap;overflow: hidden;text-overflow: ellipsis; position: relative; display: block;">' +
        item.filename +
        "</span>" +
        "<span>" +
        item.file_size +
        "KB</span>" +
        "</div>" +
        '<div class="xiaZai">' +
        "<a onclick=\"download_func('" +
        item.file_path +
        "')\">" +
        '<i class="iconfont icon-yunxiazai1"></i>' +
        "</a></div></div>" +
        "</div></div></div></div>";
    }
    const chatContentObj = crrWinObj.find(".chatContent");
    chatContentObj.append(infoHtml);
    let tt = setTimeout(function () {
      chatContentObj.scrollTop(crrWinObj[0].scrollHeight);
    }, 500);
    baguetteBox.run(".chatContent");
  }

  // 更新客服在线
  function socket_receiveOnlieUpload(msg) {
    if (msg.code !== 200) {
      return false;
    }
    let newState = msg.data.newState;
    if (newState === OnlineStatu.online) {
      $(".stateBox .dain").removeClass("state_bg_busy");
      if (!$(".stateBox .dain").hasClass("state_bg_success")) {
        $(".stateBox .dain").addClass("state_bg_success");
      }
    }
    if (newState === OnlineStatu.bebusy) {
      $(".stateBox .dain").removeClass("state_bg_success");
      if (!$(".stateBox .dain").hasClass("state_bg_busy")) {
        $(".stateBox .dain").addClass("state_bg_busy");
      }
    }

    let td_id = $("#td_" + service_id);
    if (td_id.length > 0) {
      if (newState === OnlineStatu.online) {
        td_id.find(".ustateText").text("在线");
        td_id
          .find(".uonline_statu")
          .eq(0)
          .removeClass("uonline_statu_ml")
          .addClass("uonline_statu_succcess");
      } else {
        td_id.find(".ustateText").text("忙碌");
        td_id
          .find(".uonline_statu")
          .eq(0)
          .removeClass("uonline_statu_succcess")
          .addClass("uonline_statu_ml");
      }
      td_id.find(".ustateText").attr("data-state", newState);
    }
  }

  // 监听指令
  function socket_monitorCommand(msg) {
    if (msg.code !== 200) {
      return false;
    }
    xtalert.alertInfoToast("您已被强制下线，请重新登录！");
    socket_app.close();
    window.location.href = outUrl;
  }

  // 更新名片
  function socket_receviceUploadInfoCard(msg) {
    console.log("receviceUploadCard:", msg);
    if (msg.code !== 200) {
      return false;
    }
    let msg_data = msg.data;
    setInfoCard(msg_data);
  }
});

// 获取当前聊天窗口
function ChackWinConversationId(conversation_id) {
  let crrWinObj;
  let crrIdwinSatte = false;
  if ($("#chatWindowOneConversationId").val() === conversation_id) {
    crrIdwinSatte = true;
    crrWinObj = $("#chatWindowOne");
  } else if ($("#chatWindowTwoConversationId").val() === conversation_id) {
    crrIdwinSatte = true;
    crrWinObj = $("#chatWindowTwo");
  } else if ($("#chatWindowThreeConversationId").val() === conversation_id) {
    crrIdwinSatte = true;
    crrWinObj = $("#chatWindowThree");
  }
  return [crrWinObj, crrIdwinSatte];
}

// 生成uuid
function randomUuid() {
  var s = [];
  var hexDigits = "0123456789abcdef";
  for (var i = 0; i < 36; i++) {
    s[i] = hexDigits.substr(Math.floor(Math.random() * 0x10), 1);
  }
  s[14] = "4"; // bits 12-15 of the time_hi_and_version field to 0010
  s[19] = hexDigits.substr((s[19] & 0x3) | 0x8, 1); // bits 6-7 of the clock_seq_hi_and_reserved to 01
  s[8] = s[13] = s[18] = s[23] = "-";

  return s.join("");
}

// 文件上传
function showprogress(evt) {
  var loaded = evt.loaded;
  var tot = evt.total;
  var percent = Math.floor((100 * loaded) / tot);
  var progressbar = $("#progressbar");
  progressbar.html(percent + "%");
  progressbar.attr("aria-valuenow", percent);
  progressbar.css("width", percent + "%");
}
function hideprogressbar() {
  var progressbar = $("#progressbar");
  progressbar.html("0%");
  progressbar.attr("aria-valuenow", 0);
  progressbar.css("width", "0%");
  $("#showbar").hide();
}
function post_update_statu2(action, data_uuid, msg, redi_url, get_url) {
  if (
    data_uuid == "" ||
    typeof data_uuid == "undefined" ||
    data_uuid == "undefined"
  ) {
    xtalert.alertError("要更新的ID不能为空!");
    return false;
  }
  if (action == "" || typeof action == "undefined" || action == "undefined") {
    var action = "statu";
  }
  if (typeof redi_url == "undefined" || redi_url == "undefined") {
    var redi_url = "";
  }
  if (typeof get_url == "undefined" || get_url == "undefined") {
    var get_url = "";
  }
  if (typeof msg == "undefined" || msg == "undefined") {
    var msg = "确定操作？";
  }
  xtalert.alertConfirm({
    msg: msg,
    confirmCallback: function () {
      xtajax.post({
        data: { action: action, data_uuid: data_uuid },
        success: function (data) {
          if (data.code === 200) {
            return xtalert.alertSuccessToast("操作成功！");
          } else {
            return xtalert.alertError(data.message);
          }
        },
      });
    },
  });
}

// 获取添加常用语html
function post_from_html(action, data_uuid, title, width, url) {
  Swal({
    title: false,
    text: "操作中，请稍等...",
    showCloseButton: false,
    showCancelButton: false,
    showconfirmButton: false,
    allowOutsideClick: false,
    onBeforeOpen: () => {
      Swal.showLoading();
    },
  });
  xtajax.post({
    url: url ? url : "",
    data: { action: action, data_uuid: data_uuid },
    success: function (data) {
      if (data.code === 200) {
        swal({
          title: title,
          width: width ? width : 800,
          html: data.message,
          showCancelButton: false,
          showConfirmButton: false,
          allowOutsideClick: false,
          showCloseButton: true,
          allowEscapeKey: false,
        });
      } else {
        return xtalert.alertError(data.message);
      }
    },
  });
}

// upobj:触发对象; toobj:目标对象; types:类型方法; posturl:目标url; thumb_img:修改目标img的对象;
function upload_file_func(
  upobj,
  toobj,
  action,
  posturl,
  thumb_img,
  data_uuid,
  progress,
  callbackfunc,
  is_show
) {
  if (typeof upobj == "undefined" || upobj == "undefined") {
    xtalert.alertErrorToast("upobj不能为空!");
    return false;
  }
  if (action == "" || typeof action == "undefined" || action == "undefined") {
    var action = "upimg";
  }
  if (typeof toobj == "undefined" || toobj == "undefined") {
    var toobj = "";
  }
  if (typeof posturl == "undefined" || posturl == "undefined") {
    var posturl = "";
  }
  if (typeof thumb_img == "undefined" || thumb_img == "undefined") {
    var thumb_img = "";
  }
  if (typeof data_uuid == "undefined" || data_uuid == "undefined") {
    var data_uuid = "";
  }
  if (typeof progress == "undefined" || progress == "undefined") {
    var progress = "";
  }
  var imgpath = upobj.get(0).files[0];
  if (imgpath == "") {
    xtalert.alertErrorToast("请选择文件！");
  } else {
    if (is_show) {
      Swal({
        title: false,
        text: "上传中，请稍等...",
        showCloseButton: false,
        showCancelButton: false,
        showconfirmButton: false,
        allowOutsideClick: false,
        onBeforeOpen: () => {
          Swal.showLoading();
        },
      });
    }
    // 控制进度条
    var formdata = new FormData();
    formdata.append("upload", imgpath);
    formdata.append("action", action);
    formdata.append("data_uuid", data_uuid);
    params = {
      url: posturl,
      data: formdata,
      contentType: false,
      processData: false,
      success: function (data) {
        if (data.code == 200) {
          upobj.val("");
          if (toobj) {
            toobj.val(data.message);
          }
          if (thumb_img) {
            thumb_img.attr("src", data.message);
          }
          if (callbackfunc) {
            callbackfunc(data);
          }
        } else {
          xtalert.alertError(data.message);
        }
        if (progress == "progress") {
          hideprogressbar();
        }
      },
    };
    if (progress == "progress") {
      params["progress"] = showprogress;
    }
    xtajax.post(params);
  }
}

// 取随机数
function RandomIndex(min, max, i) {
  let index = Math.floor(Math.random() * (max - min + 1) + min),
    numStart = _charStr.length - 10;
  //如果字符串第一位是数字，则递归重新获取
  if (i == 0 && index >= numStart) {
    index = RandomIndex(min, max, i);
  }
  //返回最终索引值
  return index;
}

// 生成随机字符串
function getRandomString(len) {
  let min = 0,
    max = _charStr.length - 1,
    _str = "";
  //判断是否指定长度，否则默认长度为15
  len = len || 15;
  //循环生成字符串
  for (var i = 0, index; i < len; i++) {
    index = RandomIndex(min, max, i);
    _str += _charStr[index];
  }
  return _str;
}

// 定时器
function timing_func(obj, hour, minute, second, conversation_id, is_automatic) {
  console.log(obj);
  hour = hour ? hour : 0; //小时
  minute = minute ? minute : 0; //分钟
  second = second ? second : 0; //秒

  let ctt_timing = setInterval(function () {
    //设置时间格式
    second++;
    if (second >= 60) {
      second = 0;
      minute++;
    }
    if (minute >= 60) {
      minute = 0;
      hour++;
    }
    if (hour >= 24) {
      hour = 0;
    }

    if (obj.attr("data-wdState") === "0" || obj.length <= 0) {
      return clearInterval(ctt_timing);
    }
    let timingText = "";
    if (hour >= 10) {
      timingText += hour.toString() + ":";
    } else {
      timingText += "0" + hour.toString() + ":";
    }
    if (minute >= 10) {
      timingText += minute.toString() + ":";
    } else {
      timingText += "0" + minute.toString() + ":";
    }
    if (second >= 10) {
      timingText += second.toString();
    } else {
      timingText += "0" + second.toString();
    }
    obj.find(".timingText").text(timingText);
    if (automati_creply_time != -1 && minute >= automati_creply_time || hour >= 1) {
      if (!obj.find(".timingText").hasClass("color_red")) {
        obj.find(".timingText").addClass("color_red");
      }
      if (!is_automatic || is_automatic === "" || is_automatic === false) {
        is_automatic = true;
        if ($("#" + conversation_id).length <= 0) {
          // is_automatic = true
          return clearInterval(ctt_timing);
        } else {
          xtajax.post({
            data: {
              action: "getAutomatiCreplyText",
              conversation_id: conversation_id,
            },
            success: function (data) {
              if (data.code === 200) {
                if (
                  data.data.automati_creply &&
                  data.data.automati_creply !== ""
                ) {
                  let dUid = randomUuid();
                  send_message(
                    data.data.automati_creply,
                    conversation_id,
                    true,
                    dUid
                  );
                }
                // is_automatic = true
                return clearInterval(ctt_timing);
              }
            },
          });
        }
      }
    }
  }, 1000);
}

// 消息状态定时器
function msgStatu_timing_func(msgObj) {
  let hour = 0;
  let minute = 0;
  let second = 0;
  let msgStatu_timing = setInterval(function () {
    //设置时间格式
    second++;
    if (second >= 60) {
      second = 0;
      minute++;
    }
    if (minute >= 60) {
      minute = 0;
      hour++;
    }
    if (hour >= 24) {
      hour = 0;
    }

    if (msgObj.attr("data-msgStatu") !== "0") {
      return clearInterval(msgStatu_timing);
    }

    if (second >= 30) {
      if (msgObj.attr("data-msgStatu") === "0") {
        msgObj
          .find(".msgStatu")
          .find(".iconfont")
          .removeClass("icon-jiazai2")
          .addClass("icon-shibai-01");
      }
      return clearInterval(msgStatu_timing);
    }
  }, 1000);
}

// 时间格式化
function formatDate(date, fmt) {
  if (typeof date == "string") {
    return date;
  }

  if (!fmt) fmt = "yyyy-MM-dd hh:mm:ss";

  if (!date) return null;
  var o = {
    "M+": date.getMonth() + 1, // 月份
    "d+": date.getDate(), // 日
    "h+": date.getHours(), // 小时
    "m+": date.getMinutes(), // 分
    "s+": date.getSeconds(), // 秒
    "q+": Math.floor((date.getMonth() + 3) / 3), // 季度
    S: date.getMilliseconds(), // 毫秒
  };

  if (/(y+)/.test(fmt))
    fmt = fmt.replace(
      RegExp.$1,
      (date.getFullYear() + "").substr(4 - RegExp.$1.length)
    );
  for (var k in o) {
    if (new RegExp("(" + k + ")").test(fmt))
      fmt = fmt.replace(
        RegExp.$1,
        RegExp.$1.length === 1 ? o[k] : ("00" + o[k]).substr(("" + o[k]).length)
      );
  }
  return fmt;
}

// 窗口动态处理
function winAutomationFunc(crrColseWinObj) {
  let winOne = false;
  let winOneShow = false;
  let winTwo = false;
  let winTwoShow = false;
  let winThree = false;
  let winThreeShow = false;
  let winTotal = 0;
  if ($("#chatWindowOne").css("display") !== "none") {
    winOneShow = true;
    winTotal += 1;
  }
  if ($("#chatWindowTwo").css("display") !== "none") {
    winTwoShow = true;
    winTotal += 1;
  }
  if ($("#chatWindowThree").css("display") !== "none") {
    winThreeShow = true;
    winTotal += 1;
  }

  if (crrColseWinObj.attr("id") === winOneName) {
    winOne = true;
  } else if (crrColseWinObj.attr("id") === winTwoName) {
    winTwo = true;
  } else if (crrColseWinObj.attr("id") === winThreeName) {
    winThree = true;
  }

  if (winTotal === 1) {
    $(".notChat").show();
    $(".infoBox").hide();
  }
  if (winTotal === 2) {
    let syWinObj = $("#chatWindowOne");
    if (winOne) {
      if (winTwoShow) {
        syWinObj = $("#chatWindowTwo");
        $("#chatWindowTwo").css("left", "0px");
      }
      if (winThreeShow) {
        syWinObj = $("#chatWindowThree");
        $("#chatWindowThree").css("left", "0px");
      }
    }
    if (winTwo) {
      if (winThreeShow) {
        syWinObj = $("#chatWindowThree");
        $("#chatWindowThree").css("left", "0px");
      }
    }
    if (winThree) {
      if (winTwoShow) {
        syWinObj = $("#chatWindowTwo");
        $("#chatWindowTwo").css("left", "0px");
      }
    }
    let sy_con_id = syWinObj.find(".chatWinConversationId").val();
    websocket_emit(socket_app, "serverInfoCard", {
      conversation_id: sy_con_id,
    });
    $(".chatManageBox").css("width", "calc(100% - 490px)");
    $(".infoBox").show();
  }
  if (winTotal === 3) {
    $(".chatManageBox").css("width", "calc((100% - 15px) / 2)");
    if (winOne) {
      $("#chatWindowTwo").css("left", "0px");
      $("#chatWindowThree").css("left", "calc((100% - 15px) / 2 + 10px)");
    }
    if (winTwo) {
      $("#chatWindowThree").css("left", "calc((100% - 15px) / 2 + 10px)");
    }
    if (winThree) {
      $("#chatWindowTwo").css("left", "calc((100% - 15px) / 2 + 10px)");
    }
  }
  crrColseWinObj.find(".chatWinConversationId").val("");
  crrColseWinObj.hide();
}

// 离线倒计时
function offline_timing_func(conversation_id, minute, second) {
  if(automati_close_time == -1) {
    console.log("automati_close_time is not set");
    return ;
  }
  let crr_time = new Date();
  let daTime = formatDate(crr_time, "MM-dd hh:mm");
  console.log("离线倒计时：", daTime);

  minute = minute ? minute : 0; //分钟
  second = second ? second : 0; //秒
  let conversation_obj = $("#" + conversation_id);

  let result_ls = ChackWinConversationId(conversation_id);
  const crrWinObj = result_ls[0];
  const crrIdwinSatte = result_ls[1];

  let ctl_timing = setInterval(function () {
    //设置时间格式
    second++;
    if (second >= 60) {
      second = 0;
      minute++;
    }
    let connectionState = conversation_obj.attr("data-connectionState");
    if (!connectionState || connectionState === "1") {
      return clearInterval(ctl_timing);
    }
    if ($("#" + conversation_id).length <= 0) {
      return clearInterval(ctl_timing);
    }

    let infoBoxObj = $(".infoBox");
    console.log(minute, automati_close_time);
    if (automati_close_time != -1 && minute >= automati_close_time) {
      minute = 0; //分钟
      second = 0; //秒
      if (crrIdwinSatte) {
        let crr_customer_name = crrWinObj.find(".crr_customer_name").text();
        crrWinObj.find(".site_name").text("");
        crrWinObj.find(".chatContent").find(".chat-block").remove();
        crrWinObj.find(".userportrait").hide();
        crrWinObj.find(".crr_customer_name").text("");
        crrWinObj.find(".chatWinConversationId").val("");
        if (infoBoxObj.css("display") === "block") {
          infoBoxObj.hide();
        }
        winAutomationFunc(crrWinObj);
        xtalert.alertInfo(
          "客户：" +
            crr_customer_name +
            ",已离开，会话自动结束。\n请到已结束会话列表查看聊天数据！"
        );
      } else {
        console.log("bbbbbbbbbbbbb");
        let data_wdState = conversation_obj.attr("data-wdState");
        if (data_wdState) {
          let lowWdCount = parseInt(conversation_obj.attr("data-wdCount"));
          if (lowWdCount > 0) {
            let totalWdNumber_obj = $("#totalWdNumber");
            let low_tt = $.trim(totalWdNumber_obj.text());
            totalWdNumber_obj.text((parseInt(low_tt) - lowWdCount).toString());
            totalWdNumber_obj.show();
          }
        }
      }

      conversation_obj.remove();
      if ($(".normalTab").find(".customerItem").length <= 0) {
        $(".nor_onCustomer").show();
      }

      websocket_emit(socket_app, "SetConversationState", {
        conversation_id: conversation_id,
        state: ConversationStatu.finished,
        service_id: service_id,
      });
      return clearInterval(ctl_timing);
    }
  }, 1000);
}

// 用户个人信息
function InfoUserHtml() {
  xtajax.post({
    data: { action: "info_user_html" },
    success: function (data) {
      if (data.code == 200) {
        swal({
          title: "个人信息",
          width: 800,
          html: data.message,
          showCancelButton: false,
          showConfirmButton: false,
          allowOutsideClick: false,
          showCloseButton: true,
          allowEscapeKey: false,
        });
      } else {
        return xtalert.alertError(data.message);
      }
    },
  });
}

// 提交保存个人信息
function info_user_data() {
  let portrait = $.trim($("#portrait").val());
  let telephone = $.trim($("#wintelephone").val());
  let username = $.trim($("#winusername").val());
  let nickname = $.trim($("#winnickname").val());
  let email = $.trim($("#winemail").val());
  let _beep_switch = $.trim($("#beep_switch").val());
  if (!username) {
    return xtalert.showValidationError("请输入姓名！");
  }
  let data = {
    action: "info_user_data",
    portrait: portrait,
    telephone: telephone,
    username: username,
    nickname: nickname,
    email: email,
    beep_switch: _beep_switch,
    data_uuid: service_id,
  };
  if (_beep_switch === "0") {
    beep_switch = false;
  }
  if (_beep_switch === "1") {
    beep_switch = true;
  }
  xtajax.post({
    url: userManagePageUrl,
    data: data,
    success: function (data) {
      if (data.code === 200) {
        return xtalert.alertSuccessToast("信息保存成功！");
      } else {
        return xtalert.alertError(data.message);
      }
    },
  });
}

// 修改密码
function pwd_html() {
  xtajax.post({
    data: { action: "pwd_html" },
    success: function (data) {
      if (data.code == 200) {
        swal({
          title: "修改密码",
          width: 800,
          html: data.message,
          showCancelButton: false,
          showConfirmButton: false,
          allowOutsideClick: false,
          showCloseButton: true,
          allowEscapeKey: false,
        });
      } else {
        return xtalert.alertError(data.message);
      }
    },
  });
}

// 提交修改密码
function user_pwd_func() {
  let password = $.trim($("#password").val());
  let confirmPassword = $.trim($("#confirmPassword").val());
  if (!password) {
    return xtalert.showValidationError("请输入密码！");
  }
  if (!confirmPassword) {
    return xtalert.showValidationError("请输入确认密码！");
  }
  if (password !== confirmPassword) {
    return xtalert.showValidationError("密码和确认密码不一致！");
  }
  let data = {
    action: "user_pwd_data",
    password: password,
    data_uuid: service_id,
  };
  xtajax.post({
    url: userManagePageUrl,
    data: data,
    success: function (data) {
      if (data.code === 200) {
        return xtalert.alertSuccessToast("密码修改成功！");
      } else {
        return xtalert.alertError(data.message);
      }
    },
  });
}

// 加载html
function loading_html(html_code) {
  $("#maskLayer").css("display", "flex");
  let pageUrl = "";
  let _Data = { action: "get_template_html" };
  if (html_code === "customer") {
    pageUrl = customerPageUrl;
  } else if (html_code === "chat") {
    pageUrl = chatPageUrl;
  } else if (html_code === "history") {
    pageUrl = historyPageUrl;
  } else if (html_code === "leavingMessage") {
    pageUrl = leavingMesgPageUrl;
  } else if (html_code === "setup") {
    pageUrl = settingPageUrl;
  } else if (html_code === "userManage") {
    pageUrl = userManagePageUrl;
  } else if (html_code === "blacklist") {
    pageUrl = blackListPageUrl;
  } else if (html_code === "systemlog") {
    pageUrl = systemlogListPageUrl;
  } else if (html_code === "downloadFile") {
    pageUrl = downloadFilePageUrl;
  } else {
    _Data["html_code"] = html_code;
  }
  xtajax.get({
    url: pageUrl ? pageUrl : "",
    timeout: 5000,
    data: _Data,
    success: function (data) {
      if (data.code === 200) {
        $(".appBox").empty();
        $(".appBox").append(data.data.html);
        $("#maskLayer").css("display", "none");
        if (html_code === "chat") {
          // 获取会话列表
          websocket_emit(socket_app, "conversationList", {
            service_id: service_id,
          });
        }
      } else {
        return alert("加载失败,请刷新重试！");
      }
    },
    error: function (xhr, textStatus, errorThrown) {
      if (textStatus === "timeout") {
        loading_html(html_code);
      }
    },
  });
}

// 文件下载
function download_func(fileUrl) {
  var link = document.createElement("a");
  link.setAttribute("download", "");
  link.href = fileUrl;
  link.click();
  link.remove();
}

// 开关
function switch_icon_func(obj) {
  if (obj.hasClass("icon-kaiguanguan")) {
    obj.parent().prev().val("1");
    obj.removeClass("icon-kaiguanguan").addClass("icon-kaiguan4");
  } else {
    obj.parent().prev().val("0");
    obj.removeClass("icon-kaiguan4").addClass("icon-kaiguanguan");
  }
}

// 退出登录
function login_out() {
  xtalert.alertConfirm({
    msg: "确定退出登录？",
    confirmCallback: function () {
      window.location.href = login_out_url;
    },
  });
}

// 更新语言
function updateLanguage(language, title, msg) {
  xtalert.alertConfirm({
    title: title,
    msg: msg,
    confirmCallback: function () {
      xtajax.post({
        url: userManagePageUrl,
        data: {
          action: "update_language",
          language: language,
          data_uuid: service_id,
        },
        success: function (data) {
          if (data.code === 200) {
            xtalert.alertSuccessToast();
            window.location.reload();
          } else {
            return xtalert.alertError(data.message);
          }
        },
      });
    },
  });
}

function setInfoCard(msg_data) {
  if (msg_data.client_type === "pc") {
    $(".clientType img").attr("src", "/assets/chat/images/computer.png");
    $(".clientType span").last().text("电脑");
  } else {
    $(".clientType img").attr("src", "/public/chat/images/phone.png");
    $(".clientType span").last().text("手机");
  }

  if (msg_data.os_type === "windows") {
    $(".systemType img").attr("src", "/assets/chat/images/Windows.png");
    $(".systemType").find("span").last().text("Windows");
  } else if (msg_data.os_type === "linux") {
    $(".systemType img").attr("src", "/assets/chat/images/linux.png");
    $(".systemType").find("span").last().text("Linux");
  } else if (msg_data.os_type === "mac os x") {
    $(".systemType img").attr("src", "/assets/chat/images/ios.png");
    $(".systemType").find("span").last().text("macOs");
  }

  if (msg_data.browser_type === "chrome") {
    $(".browserType img").show();
    $(".browserType .iconfont").hide();
    $(".browserType img").attr("src", "/assets/chat/images/guge.png");
    $(".browserType span").last().text("谷歌");
  } else if (msg_data.browser_type === "firefox") {
    $(".browserType img").show();
    $(".browserType .iconfont").hide();
    $(".browserType img").attr("src", "/assets/chat/images/firefox.png");
    $(".browserType span").last().text("火狐");
  } else if (msg_data.browser_type === "safari") {
    $(".browserType img").show();
    $(".browserType .iconfont").hide();
    $(".browserType img").attr("src", "/assets/chat/images/Safari.png");
    $(".browserType span").last().text("Safari");
  } else {
    $(".browserType img").hide();
    $(".browserType .iconfont").show();
    $(".browserType span").last().text("未知浏览器");
  }

  $(".ip span").last().text(msg_data.ip);
  $(".ipPosition span").text(msg_data.track ? msg_data.track : "未知");
  $(".mingPian").show();
  $(".sheBei").show();

  let customer_data = msg_data.customer_data;
  $("#username").val(customer_data.username);
  if (customer_data.gender == "male") {
    $("#male").attr("checked", true);
  } else if (customer_data.gender == "male") {
    $("#female").attr("checked", true);
  }
  $("#email").val(customer_data.email);
  $("#telephone").val(customer_data.telephone);
  $("#telegram").val(customer_data.telegram);
  $("#address").val(customer_data.address);

  const selectElement = $("#category");
  // Clear any existing options
  selectElement.empty();
  // Add new options based on the categories array
  $.each(msg_data.categories, function (index, category) {
    let selected = "";
    if (customer_data.category === category.category) selected = "selected";
    selectElement.append(
      `<option value=${category.category} ${selected}>${category.category}</option>`
    );
  });

  $("#note").val(customer_data.note);
  if (customer_data.gender == "male") {
    $("#male").prop("checked", true);
  }
  if (customer_data.gender == "female") {
    $("#female").prop("checked", true);
  }
}
