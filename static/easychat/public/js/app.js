$(function () {
  function websocket_emit(ws, event_id, data) {
      if (ws.readyState === WebSocket.OPEN) {
          sendData = {
              event_id,
              data,
          };
          ws.send(JSON.stringify(sendData));
      } else {
          console.log("WebSocket is not in OPEN state.");
      }
  }

  // 缓存机制
  var foowwLocalStorage = {
      set: function (key, value, ttl_ms) {
          var data = { value: value, expirse: new Date(ttl_ms).getTime() };
          localStorage.setItem(key, JSON.stringify(data));
      },
      get: function (key) {
          var data = JSON.parse(localStorage.getItem(key));
          if (data !== null) {
              // debugger
              if (data.expirse != null && data.expirse < new Date().getTime()) {
                  localStorage.removeItem(key);
              } else {
                  return data.value;
              }
          }
          return null;
      },
  };

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

  // 时间格式化
  function formatDate(date, fmt) {
      if (typeof date == "string") {
          return date;
      }

      if (!fmt) fmt = "yyyy-MM-dd hh:mm:ss";

      if (!date || date == null) return null;
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
          fmt = fmt.replace(RegExp.$1, (date.getFullYear() + "").substr(4 - RegExp.$1.length));
      for (var k in o) {
          if (new RegExp("(" + k + ")").test(fmt))
              fmt = fmt.replace(RegExp.$1, RegExp.$1.length === 1 ? o[k] : ("00" + o[k]).substr(("" + o[k]).length));
      }
      return fmt;
  }

  // 日期格式化：月-日 时：分：秒
  function getShiQuTime(msgtime) {
      let timezoneOffset = 0 - new Date().getTimezoneOffset() / 60;
      let ddl = msgtime.replace(/-/g, "/");
      let dvv = new Date(ddl);
      const TODAY = new Date(dvv.setHours(dvv.getHours() + timezoneOffset));
      return formatDate(TODAY, "MM-dd hh:mm");
  }

  // 上传文件
  function upload_file() {
      let filepathObj = $("#filepath");
      var imgpath = filepathObj.get(0).files[0];
      if (imgpath === "") {
          alert("请选择文件！");
      } else {
          var formdata = new FormData();
          formdata.append("upload", imgpath);
          formdata.append("site_code", sessionCode);
          formdata.append("filename", imgpath.name);
          formdata.append("filesize", imgpath.size);
          formdata.append("action", "uploadImage");
          params = {
              data: formdata,
              contentType: false,
              processData: false,
              success: function (data) {
                  if (data.code === 200) {
                      filepathObj.val("");
                      $("#problemImage").val(data.message);
                      $(".demoIMage img").attr("src", data.message);
                      $(".uploadImageb").hide();
                      $(".demoIMage").show();
                  } else {
                      xtalert.alertError(data.message);
                  }
              },
          };
          xtajax.post(params);
      }
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

  var socket_app;
  var is_first_connection = true;
  ////////////////////////////////////////////////////////////////////////////////////////////////
  function setupWebSocket() {
      socket_app = new WebSocket(`${location.protocol.replace("http", "ws")}//${document.domain}:${location.port}/chat`);

      socket_app.onopen = function () {
          let crrtiem = new Date();
          console.log("Successfully connected！", crrtiem);

          if (fastState && !foowwLocalStorage.get(chatUsidKey) && !foowwLocalStorage.get(chatSessionKey)) {
              $("#fastBox").show();
              $("#account").parent().show();
              $("#czTime").parent().show();
              $("#problemImage").parent().parent().show();
              $("#cjhdText").parent().parent().hide();
              $("#txTme").parent().hide();
              $(".blockScreen").hide();
          }
          else {
              send_request_init();
          }
          pingTimerId = setInterval(send_ping, 50000);
      };

      socket_app.onerror = function () {
          console.log("Websocket error occured");
      };

      socket_app.onclose = function () {
          clearInterval(pingTimerId);
          let crrtiem = new Date();
          console.log("Websocket is disconncted and reconnecting now...", crrtiem);
          setTimeout(setupWebSocket, 1000);
      };

      socket_app.onmessage = (event) => {
          const jsonData = JSON.parse(event.data);
          event_id = jsonData.event_id;
          msg = jsonData.msg;

          switch (event_id) {
              case "initResponse":
                  socket_initResponse(msg);
                  break;
              case "chatReceiveServiceMessage":
                  socket_chatReceiveServiceMessage(msg);
                  break;
              case "chatUploadFeedback":
                  socket_chatUploadFeedback(msg);
                  break;
              case "chatReceiveServerFeedback":
                  socket_chatReceiveServerFeedback(msg);
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

  // 请求初始化访客信息
  function send_request_init() {
      let infoData = {
          site_code: sessionCode,
      };
      if (foowwLocalStorage.get(chatUsidKey)) {
          infoData["chatUsid"] = foowwLocalStorage.get(chatUsidKey);
      }
      if (foowwLocalStorage.get(chatSessionKey)) {
          infoData["chatSession"] = foowwLocalStorage.get(chatSessionKey);
      }
      websocket_emit(socket_app, "initVisitor", infoData);
  }

  // 快捷进入客服
  function advance_chat_func() {
      $(".blockScreen").show();
      $("#fastBox").hide();
      send_request_init();
  }

  // 提交快捷信息
  function subFastFunc() {
      let problem = $.trim($("input[name='problem']:checked").val());
      let account = $.trim($("#account").val());
      let txTme = $.trim($("#txTme").val());
      let czTime = $.trim($("#czTime").val());
      let cjhdText = $.trim($("#cjhdText").val());
      let problemImage = $.trim($("#problemImage").val());
      if (!account) {
          return alert("请输入账户！");
      }
      let infoData = {
          site_code: sessionCode,
          problem: problem,
          account: account,
      };
      if (problem === "czwt") {
          if (!czTime) {
              return alert("请选择充值时间！");
          }
          if (!problemImage) {
              return alert("请上传充值图片！");
          }
          infoData["czTime"] = czTime;
          infoData["problemImage"] = problemImage;
      } else if (problem === "txwt") {
          if (!txTme) {
              return alert("请选择统计时间！");
          }
          if (!problemImage) {
              return alert("请上传充值图片！");
          }
          infoData["txTme"] = txTme;
          infoData["problemImage"] = problemImage;
      } else if (problem === "cjsq") {
          if (!cjhdText) {
              return alert("请输入内容！");
          }
          infoData["cjhdText"] = cjhdText;
      }
      if (foowwLocalStorage.get(chatUsidKey)) {
          infoData["chatUsid"] = foowwLocalStorage.get(chatUsidKey);
      }
      if (foowwLocalStorage.get(chatSessionKey)) {
          infoData["chatSession"] = foowwLocalStorage.get(chatSessionKey);
      }
      websocket_emit(socket_app, "initVisitor", infoData);
      $(".blockScreen").show();
  }

  function postAutoQuestion(question) {
      let chatUsid = foowwLocalStorage.get(chatUsidKey);
      let chatSession = foowwLocalStorage.get(chatSessionKey);

      if (!question) {
          return alert("请输入内容！");
      }
      let dd = randomUuid();

      websocket_emit(socket_app, "chatReceiveMessage", {
          text: question,
          uuid: dd,
          chatSession: chatSession,
          chatUsid: chatUsid,
          type: "text",
      });

      websocket_emit(socket_app, "realTimeInputMessage", {
          text: "",
          chatSession: chatSession,
          chatUsid: chatUsid,
      });

      let html = "";
      let crr_time = new Date();
      let daTime = formatDate(crr_time, "MM-dd hh:mm");
      html +=
          '<div class="chat-block chatR">' +
          '<div class="inside">' +
          '<img src="/public/chat/images/user.png" alt="" class="userImage">' +
          '<div class="chatting-right"><div class="chat-content">' +
          '<div class="rightText">' +
          question +
          "</div>" +
          '<div class="time">' +
          daTime +
          "</div>" +
          "</div></div></div></div>";
      $(".chatMeassge").append(html);
      $(".chatMeassge").scrollTop($(".chatMeassge")[0].scrollHeight);
      $("#textContent").val("");
  }

  window.postAutoQuestion = postAutoQuestion;
  // 聊天窗口激活反馈
  function customerWinFocus_func() {
      let infoData = {
          site_code: sessionCode,
      };
      if (foowwLocalStorage.get(chatUsidKey)) {
          infoData["chatUsid"] = foowwLocalStorage.get(chatUsidKey);
      }
      if (foowwLocalStorage.get(chatSessionKey)) {
          infoData["chatSession"] = foowwLocalStorage.get(chatSessionKey);
      }
      websocket_emit(socket_app, "customerWinFocus", infoData);
  }

  $.single_time(".selectTiime");

  // 快捷问题选择监控
  $("input[type='radio']").on("click", function () {
      let problem = $.trim($("input[name='problem']:checked").val());
      $(".demoIMage img").attr("src", "");
      $(".uploadImageb").show();
      if (problem === "czwt") {
          $("#account").parent().show();
          $("#czTime").parent().show();
          $("#problemImage").parent().parent().show();
          $("#cjhdText").parent().parent().hide();
          $("#txTme").parent().hide();
      } else if (problem === "txwt") {
          $("#account").parent().show();
          $("#txTme").parent().show();
          $("#problemImage").parent().parent().show();
          $("#cjhdText").parent().parent().hide();
          $("#czTime").parent().hide();
      } else if (problem === "cjsq") {
          $("#account").parent().show();
          $("#cjhdText").parent().parent().show();
          $("#problemImage").parent().parent().hide();
          $("#txTme").parent().hide();
          $("#czTime").parent().hide();
      } else if (problem === "qtwt") {
          $("#account").parent().hide();
          $("#cjhdText").parent().parent().hide();
          $("#problemImage").parent().parent().hide();
          $("#txTme").parent().hide();
          $("#czTime").parent().hide();
          $(".subBtn").hide();
          $(".enterBtn").show();
      }
  });

  // 关闭窗口时弹出确认提示
  $(window).bind("beforeunload", function () {
      // 只有在标识变量is_confirm不为false时，才弹出确认提示
      // if(window.is_confirm !== false){}
      return "您可能有数据没有保存!";
  });

  // 浏览器是去焦点时触发
  window.onblur = function (e) {
      windowFocusStatu = false;
  };

  // 浏览器获得焦点时触发
  window.onfocus = function (e) {
      windowFocusStatu = true;
      customerWinFocus_func();
  };

  // 点击打分
  $(".levelLi").on("click", function () {
      $(this).addClass("active").siblings().removeClass("active");
  });

  function send_ping() {
      websocket_emit(socket_app, "ping", "ping")
  }
  let pingTimerId = 0;

  // 接收初始化数据
  function socket_initResponse(msg) {
      if (msg.code === 200) {
          let back_data = msg.data;

          if (is_first_connection) {
              is_first_connection = false;
              if (back_data.problems.length > 0)
                  $.each(back_data.problems, function (i, item) {
                      let problem_item_html = "";
                      problem_item_html = `<button onclick="window.postAutoQuestion('${item.title}')">+ ${item.title}</button>`;
                      $("#chatAutoReplyProblems").append(problem_item_html);
                  });
              else {
                  $("#chatAutoReplyProblems").css("padding", "0px");
                  $(".chatMeassge").css("height", "calc(100% - 6.3rem)");
              }
          }

          chatConfig["service_data"] = back_data.service_data;
          chatConfig["is_score"] = back_data.is_score;
          if (!back_data.service_state) {
              $(".blockScreen").hide();
              $(".LeaveMessage").show();
          } else {
              foowwLocalStorage.set(
                  chatSessionKey,
                  back_data.chatSession,
                  new Date().getTime() + 60000 * 60 * 24
              );
              $(".LeaveMessage").hide();
              $("#containter").show();

              if (back_data.is_score) {
                  $(".evaluateForm").hide();
                  $(".evaluateSuccess").show();
                  $(".scoreSubLoading").css("display", "none");
                  $(".scoreSuccessBox").css("display", "flex");
              }

              if (back_data.service_data.portrait) {
                  $(".servicePortrait").attr("src", back_data.service_data.portrait);
                  service_portrait = back_data.service_data.portrait;
              } else {
                  $(".servicePortrait").attr(
                      "src",
                      "/public/chat/portrait/photo_chat.jpg"
                  );
                  service_portrait = "/public/chat/portrait/photo_chat.jpg";
              }
              $(".serviceName").text(back_data.service_data.service_name);

              $(".chatMeassge").find(".chat-block").remove();
              
              $.each(back_data.messageList, function (i, item) {
                  let mhtml = "";
                  if (item.is_service) {
                      if (item.content_type === "text") {
                          mhtml +=
                              '<div class="chat-block chatL"' +
                              ' data-uuid="' +
                              item.dataId +
                              '">' +
                              '<div class="inside">' +
                              '<img src="' +
                              service_portrait +
                              '" alt="" class="userImage">' +
                              '<div class="chat-name">' +
                              back_data.service_data.service_name +
                              "</div>" +
                              '<div class="chatting-left"><div class="chat-content">' +
                              '<div class="leftText">' +
                              item.text +
                              "</div>" +
                              '<div class="time">' +
                              getShiQuTime(item.create_time) +
                              "</div>" +
                              "</div></div></div></div>";
                      } else if (item.content_type === "picture") {
                          mhtml +=
                              '<div class="chat-block chatL"' +
                              ' data-uuid="' +
                              item.dataId +
                              '">' +
                              '<div class="inside">' +
                              '<img src="' +
                              service_portrait +
                              '" alt="" class="userImage">' +
                              '<div class="chat-name">' +
                              back_data.service_data.service_name +
                              "</div>" +
                              '<div class="chatting-left">' +
                              '<div class="chat-content chat-content-img">' +
                              '<a href="' +
                              item.file_path +
                              '"><img src="' +
                              item.file_path +
                              '" alt=""></a>' +
                              '<div class="time">' +
                              getShiQuTime(item.create_time) +
                              "</div>" +
                              "</div></div></div></div>";
                      }
                      else if (item.content_type === "video") {
                        mhtml +=
                            '<div class="chat-block chatL"' +
                            ' data-uuid="' +
                            item.dataId +
                            '">' +
                            '<div class="inside">' +
                            '<img src="' +
                            service_portrait +
                            '" alt="" class="userImage">' +
                            '<div class="chat-name">' +
                            back_data.service_data.service_name +
                            "</div>" +
                            '<div class="chatting-left">' +
                            '<div class="chat-content">' +
                            '                                       <video width="400" height="auto" controls> ' +
                            "<source src='" +
                            item.file_path +
                            '\' type="video/mp4"/>' +
                            "</video>" +
                            "</div></div></div></div>";
                    } 
                      else if (item.content_type === "file") {
                          mhtml +=
                              '<div class="chat-block chatL"' +
                              ' data-uuid="' +
                              item.dataId +
                              '">' +
                              '<div class="inside">' +
                              '<img src="' +
                              service_portrait +
                              '" alt="" class="userImage">' +
                              '<div class="chat-name">' +
                              back_data.service_data.service_name +
                              "</div>" +
                              '<div class="chatting-left">' +
                              '<div class="chat-content">' +
                              '<div class="chatFile">' +
                              '<div style="position: relative; height: 75px; overflow: hidden;"><i class="iconfont icon-wenjian" style="font-size: 49px; line-height: 75px;"></i></div>' +
                              '<div style="position: relative; display: flex; flex-direction: column; justify-content: flex-start; font-size: 13px; line-height: 20px; margin-left: 10px; color: #81878a;">' +
                              '<span style="margin-bottom: 3px;">' +
                              item.filename +
                              "</span>" +
                              "<span>" +
                              item.file_size + 'KB' + 
                              '<time class="time" style="vertical-align: -2px; margin-left: 40px; top: 1px;">' +
                              getShiQuTime(item.create_time) +
                              "</time></span>" +
                              "</div>" +
                              '<div class="downloadBtn" onclick="download_func(\'' +
                              item.file_path +
                              "')\">" +
                              "<span>下载</span>" +
                              "</div></div></div></div></div>";
                      }
                  }
                  if (item.is_customer) {
                      if (item.content_type == "text") {
                          mhtml +=
                              '<div class="chat-block chatR">' +
                              '<div class="inside">' +
                              '<img src="/public/chat/images/user.png" alt="" class="userImage">' +
                              '<div class="chatting-right"><div class="chat-content">' +
                              '<div class="rightText">' +
                              item.text +
                              "</div>" +
                              '<div class="time">' +
                              getShiQuTime(item.create_time) +
                              "</div>" +
                              "</div></div></div></div>";
                      } else if (item.content_type == "picture") {
                          mhtml +=
                              '<div class="chat-block chatR">' +
                              '<div class="inside">' +
                              '<img src="/public/chat/images/user.png" alt="" class="userImage">' +
                              '<div class="chatting-right">' +
                              '<div class="chat-content chat-content-img">' +
                              '<a href="' +
                              item.file_path +
                              '"><img src="' +
                              item.file_path +
                              '" alt=""></a>' +
                              '<div class="time">' +
                              getShiQuTime(item.create_time) +
                              "</div>" +
                              "</div></div></div></div>";
                      } else if (item.content_type == "video") {
                          mhtml +=
                              '                    <div class="chat-block chatR">' +
                              '                        <div class="inside">' +
                              '                            <img src="/public/chat/images/user.png" alt="" class="userImage">' +
                              '                            <div class="chatting-right">' +
                              '                                <div class="chat-content">' +
                              '                                    <div class="chatFile">' +
                              '                                        <div style="position: relative; height: 70px; overflow: hidden;">\n' +
                              '                                            <i class="iconfont icon-shipin2" style="font-size: 39px; line-height: 75px;"></i>\n' +
                              "                                        </div>\n" +
                              '                                        <div style="position: relative; display: flex; flex-direction: column; justify-content: flex-start; font-size: 13px; line-height: 20px; margin-left: 15px; color: #FFFFFF;">\n' +
                              '                                            <div style="margin-bottom: 3px; position: relative;white-space: nowrap;overflow: hidden;text-overflow: ellipsis;max-width: 100px;">' +
                              item.filename +
                              "</div>\n" +
                              '                                            <div style="position: relative; display: flex;">' +
                              item.file_size +
                              'KB<time class="time" style="vertical-align: -2px; margin-left: 40px; top: 1px;">' +
                              getShiQuTime(item.create_time) +
                              "</time></div>\n" +
                              "                                        </div>\n" +
                              "                                    </div>\n" +
                              "                                </div>\n" +
                              "                            </div>\n" +
                              "                        </div>\n" +
                              "                    </div>";
                      }
                  }
                  if (mhtml.length > 0) {
                      $(".chatMeassge").append(mhtml);
                  }
              });
              baguetteBox.run(".chatMeassge");
              let tt2 = setTimeout(function () {
                  $(".chatMeassge").scrollTop($(".chatMeassge")[0].scrollHeight);
              }, 500);
              $(".blockScreen").hide();
          }

          let site_data = back_data.site_data;
          if (site_data) {
              if (site_data.site_right_info_back_color) {
                  $(".problemBox").css(
                      "background-color",
                      site_data.site_right_info_back_color
                  );
              }
              if (site_data.site_right_info_img) {
                  $(".problemBox .advertisement")
                      .find("img")
                      .attr("src", site_data.site_right_info_img);
              } else {
                  $(".problemBox .advertisement").find("img").hide();
              }

              if (site_data.site_main_color) {
                  $(".evaluateForm .subComment").css(
                      "background-color",
                      site_data.site_main_color
                  );
                  $(".chatTextBox .optionBtn").css(
                      "background-color",
                      site_data.site_main_color
                  );
                  $(".TextBox .iconfont").css("color", site_data.site_main_color);
              }
              if (site_data.site_title) {
                  $("title").text(site_data.site_title);
              }
              if (site_data.site_icon) {
                  $("link[rel='icon']").attr("href", site_data.site_icon);
              }
              if (site_data.site_announcement) {
                  $("#site_announcement").parent().show();
                  $("#site_announcement").append(site_data.site_announcement);
              } else {
                  $("#site_announcement").parent().hide();
              }
          }

          foowwLocalStorage.set(
              chatUsidKey,
              back_data.chatUsid,
              new Date().getTime() + 60000 * 60 * 24
          );
          console.log("连接初始化成功！");
      } else {
          $("body").empty();
          console.log("连接初始化失败！");
      }
  }

  // 接收客服message
  function socket_chatReceiveServiceMessage(msg) {
      let sHtml = "";
      if (msg.content_type === "text") {
          sHtml +=
              '<div class="chat-block chatL"' +
              ' data-uuid="' +
              msg.dataId +
              '">' +
              '<div class="inside">' +
              '<img src="' +
              service_portrait +
              '" alt="" class="userImage">' +
              '<div class="chat-name">' +
              chatConfig.service_data.service_name +
              "</div>" +
              '<div class="chatting-left"><div class="chat-content">' +
              '<div class="leftText">' +
              msg.text +
              "</div>" +
              '<div class="time">' +
              getShiQuTime(msg.create_time) +
              "</div>" +
              "</div></div></div></div>";
      } else if (msg.content_type === "picture") {
          sHtml +=
              '<div class="chat-block chatL"' +
              ' data-uuid="' +
              msg.dataId +
              '">' +
              '<div class="inside">' +
              '<img src="' +
              service_portrait +
              '" alt="" class="userImage">' +
              '<div class="chat-name">' +
              chatConfig.service_data.service_name +
              "</div>" +
              '<div class="chatting-left">' +
              '<div class="chat-content chat-content-img">' +
              '<a href="' +
              msg.file_path +
              '"><img src="' +
              msg.file_path +
              '" alt=""></a>' +
              '<div class="time">' +
              getShiQuTime(msg.create_time) +
              "</div>" +
              "</div></div></div></div>";
      } 
      else if (msg.content_type === "video") {
        sHtml +=
            '<div class="chat-block chatL"' +
            ' data-uuid="' +
            msg.dataId +
            '">' +
            '<div class="inside">' +
            '<img src="' +
            service_portrait +
            '" alt="" class="userImage">' +
            '<div class="chat-name">' +
            chatConfig.service_data.service_name +
            "</div>" +
            '<div class="chatting-left">' +
            '<div class="chat-content">' +

            '                                       <video width="400" height="auto" controls> ' +
            "<source src='" +
            msg.file_path +
            '\' type="video/mp4"/>' +
            "</video>" +

            "</div></div></div></div>";
        }
      else if (msg.content_type === "file") {
          sHtml +=
              '<div class="chat-block chatL"' +
              ' data-uuid="' +
              msg.dataId +
              '">' +
              '<div class="inside">' +
              '<img src="' +
              service_portrait +
              '" alt="" class="userImage">' +
              '<div class="chat-name">' +
              chatConfig.service_data.service_name +
              "</div>" +
              '<div class="chatting-left">' +
              '<div class="chat-content">' +
              '<div class="chatFile">' +
              '<div style="position: relative; height: 75px; overflow: hidden;"><i class="iconfont icon-file-word-fill" style="font-size: 49px; line-height: 75px;"></i></div>' +
              '<div style="position: relative; display: flex; flex-direction: column; justify-content: flex-start; font-size: 13px; line-height: 20px; margin-left: 10px; color: #81878a;">' +
              '<span style="margin-bottom: 3px;">' +
              msg.filename +
              "</span>" +
              "<span>" +
              msg.file_size +
              '<time class="time" style="vertical-align: -2px; margin-left: 40px; top: 1px;">' +
              getShiQuTime(msg.create_time) +
              "</time></span>" +
              "</div>" +
              '<div class="downloadBtn" onclick="download_func(\'' +
              msg.file_path +
              "')\">" +
              "<span>下载</span>" +
              "</div></div></div></div></div>";
      }

      if (windowFocusStatu) {
          customerWinFocus_func();
      }

      $(".chatMeassge").append(sHtml);
      baguetteBox.run(".chatMeassge");
      let tt = setTimeout(function () {
          $(".chatMeassge").scrollTop($(".chatMeassge")[0].scrollHeight);
      }, 500);
  }

  // 上传图片反馈
  function socket_chatUploadFeedback(msg) {
      let state = msg.state;
      let _data = msg.data;
      if (state !== 200) {
          return;
      }
      let uoloadCode = _data.uoloadCode;
      let file_path = _data.file_path;
      if (!uoloadCode) {
          return;
      }
      let imgObj = $("#" + uoloadCode);
      imgObj.find(".loading").hide();
      imgObj.find("a").attr("href", file_path).show();
      imgObj.find("a").find("img").attr("src", file_path);
      baguetteBox.run(".chatMeassge");
      let tt = setTimeout(function () {
          $(".chatMeassge").scrollTop($(".chatMeassge")[0].scrollHeight);
      }, 500);
  }

  // 接收服务器反馈
  function socket_chatReceiveServerFeedback(msg) {
      let result_data = msg.data;
      let action = result_data.action;
      if (action === "left_customer_score") {
          // 左侧评论反馈
          $(".evaluateForm").hide();
          $(".evaluateSuccess").show();
          $(".scoreSubLoading").css("display", "none");
          $(".scoreSuccessBox").css("display", "flex");
      } else if (action === "serverUploadFeedback") {
          // 客户端上次文件，反馈
          if (msg.code === 200) {
              let _data = msg.data;
              let uoloadCode = _data.uoloadCode;
              let file_path = _data.file_path;
              if (!uoloadCode) {
                  return;
              }
              let imgObj = $("#" + uoloadCode);
              imgObj.find(".loading").hide();
              imgObj.find("a").attr("href", file_path).show();
              imgObj.find("a").find("img").attr("src", file_path);
              imgObj.find(".time").show();
              baguetteBox.run(".chatMeassge");
              let tt = setTimeout(function () {
                  let chatM = $(".chatMeassge");
                  chatM.scrollTop(chatM[0].scrollHeight);
              }, 500);
          }
      } else if (action === "finish_conversation") {
          // 结束对话评论，处理反馈
          if (msg.code === 200) {
              alert("已结束对话！");
              $("#diaShade").hide(0);
              $(".chatTextBox").hide(0);
              $(".chatFinishTextBox").show(0);
          }
      } else if (action === "serviceColseChat") {
          // 服务端主动结束会话
          if (result_data.score_state) {
              $("#diaShade").hide(0);
              $(".chatTextBox").hide(0);
              $(".chatFinishTextBox").show(0);
          } else {
              $(".chatTextBox").hide(0);
              $(".chatFinishTextBox").show(0);
              $("#diaShade").show(0);
              $(".dialogWrapDanFu").show();
              $(".confirmModal").hide();
              $("#colse_dialogWrapDanFu").hide();
          }
      } else if (action === "serviceRetractMessage") {
          // 服务器主动撤回消息
          const crr_messageObj = $("div[data-uuid='" + result_data.dataId + "']");
          // const html = '<div style="display: block; text-align: center; font-size: 12px; color: rgb(153, 153, 153); margin-top: 10px;">对方，撤回了一条消息</div>'
          // crr_messageObj.empty().append(html)
          crr_messageObj.empty();
      } else if (action === "serverReply") {
          if (result_data.statu === "ongoing") {
              let htmll =
                  '<p class="serverReplyStatu" style="line-height: 30px;margin-left: 25px;text-align: left;font-size: 14px;">' +
                  zzsrz +
                  "</p>";
              $(".serverReplyStatu").remove();
              $(".chatMeassge")
                  .find(".chatL")
                  .eq(-1)
                  .find(".chatting-left")
                  .append(htmll);
          } else {
              $(".serverReplyStatu").remove();
          }
      }
  }

  //jQuery实时监听input值变化
  $("#textContent").on("input valuechange", function () {
      let strText = $.trim($(this).val());
      let chatUsid = foowwLocalStorage.get(chatUsidKey);
      let chatSession = foowwLocalStorage.get(chatSessionKey);
      websocket_emit(socket_app, "realTimeInputMessage", {
          text: strText,
          chatSession: chatSession,
          chatUsid: chatUsid,
      });
  });

  // 点击发送
  $("#faSongBtn").on("click", function () {
      let chatUsid = foowwLocalStorage.get(chatUsidKey);
      let chatSession = foowwLocalStorage.get(chatSessionKey);
      let textMag = $.trim($("#textContent").val());
      if (!textMag) {
          return alert("请输入内容！");
      }
      websocket_emit(socket_app, "chatReceiveMessage", {
          text: textMag,
          chatSession: chatSession,
          chatUsid: chatUsid,
          type: "text",
      });
      websocket_emit(socket_app, "realTimeInputMessage", {
          text: "",
          chatSession: chatSession,
          chatUsid: chatUsid,
      });
      let html = "";
      let crr_time = new Date();
      let daTime = formatDate(crr_time, "MM-dd hh:mm");
      html +=
          '<div class="chat-block chatR">' +
          '<div class="inside">' +
          '<img src="/public/chat/images/user.png" alt="" class="userImage">' +
          '<div class="chatting-right"><div class="chat-content">' +
          '<div class="rightText">' +
          textMag +
          "</div>" +
          '<div class="time">' +
          daTime +
          "</div>" +
          "</div></div></div></div>";
      $(".chatMeassge").append(html);
      $(".chatMeassge").scrollTop($(".chatMeassge")[0].scrollHeight);
      $("#textContent").val("");
  });

  // 回车键发送消息
  $("#textContent").keydown(function (e) {
      if (e.ctrlKey == true && e.key == "Enter") {
          var mtxt = $("#textContent");
          mtxt.val(mtxt.val() + "\n");
      } else if (e.key == "Enter" && !e.ctrlKey) {
          e.preventDefault();
          $("#faSongBtn").click();
      }
  });

  // 发送图片触发函数
  $("#uploadfile").on("change", function () {
      let objt = $("#uploadfile");
      let chatUsid = foowwLocalStorage.get(chatUsidKey);
      let chatSession = foowwLocalStorage.get(chatSessionKey);
      if (objt.get(0).files.length <= 0) {
          return;
      }
      let file = objt.get(0).files[0];
      let filename = objt.get(0).files[0].name;
      let filesize = objt.get(0).files[0].size;
      let _ftype_arr = filename.split(".");
      let _ftype = _ftype_arr[_ftype_arr.length - 1];
      let _ftype_to = "." + _ftype.toLocaleLowerCase();
      let imgindex = $.inArray(_ftype_to, image_types);
      let videoindex = $.inArray(_ftype_to, video_types);
      console.log(filename);
      $("#uploadfile").val("");
      if (filesize > file_size) {
          return alert("文件过大！");
      }
      if (imgindex >= 0) {
          return send_chat_images(
              file,
              chatUsid,
              chatSession,
              filename,
              filesize
          );
      } else if (videoindex >= 0) {
          return snd_chat_video(
              file,
              chatUsid,
              chatSession,
              filename,
              filesize
          );
      } else {
          return alert("文件格式错误!~~~~~" + filename);
      }
  });

  // 提交评论
  $("#subCommentBtn").on("click", function () {
      if ($(".pingFen").find(".active").length <= 0) {
          return alert("请选择评分等级！");
      }
      let level = parseInt($(".pingFen").find(".active").attr("data-fenshu"));
      let cntText = $.trim($("#commentText").val());
      if (!cntText) {
          return alert("请输入评分内容！");
      }
      let chatUsid = foowwLocalStorage.get(chatUsidKey);
      let chatSession = foowwLocalStorage.get(chatSessionKey);
      let _data = {
          action: "left_customer_score",
          level: level,
          cntText: cntText,
          chatUsid: chatUsid,
          chatSession: chatSession,
      };
      $(".evaluateForm").hide();
      $(".evaluateSuccess").show();
      $(".scoreSubLoading").css("display", "block");
      $(".scoreSuccessBox").css("display", "none");

      //console.log(_data)
      websocket_emit(socket_app, "customerScore", _data);
  });

  // 结束会话
  $("#finishConversation").on("click", function () {
      $("#diaShade").show();
      $(".dialogWrapDanFu").hide();
      $(".promptBox").find(".xw").show();
      $(".promptBox").find("img").hide();
      $(".confirmModal").show();
  });
  $(".cancelBtn").on("click", function () {
      $("#diaShade").hide();
  });
  $(".confirmBtn").on("click", function () {
      if ($(".promptBox").find(".xw").css("display") === "block") {
          let chatUsid = foowwLocalStorage.get(chatUsidKey);
          let chatSession = foowwLocalStorage.get(chatSessionKey);
          let _data = {
              chatUsid: chatUsid,
              chatSession: chatSession,
          };
          //websocket_emit(socket_app, 'finishConversation',_data);
          if (chatConfig.is_score) {
              $("#diaShade").hide();
              let _data = {
                  chatUsid: chatUsid,
                  chatSession: chatSession,
              };
              websocket_emit(socket_app, "finishConversation", _data);
          } else {
              $("#diaShade").show();
              $(".dialogWrapDanFu").show();
              $(".confirmModal").hide();
          }
      } else if ($(".promptBox").find("img").css("display") !== "none") {
          $(".promptBox").find("img").attr("src", "");
          $(".promptBox").find("img").css("display", "none");
          $("#diaShade").hide();
          $(".dialogWrapDanFu").hide();
          $(".confirmModal").hide();

          let filename = clipboardFile.name;
          let filesize = clipboardFile.size;
          let _ftype_arr = filename.split(".");
          let _ftype = _ftype_arr[_ftype_arr.length - 1];
          let _ftype_to = "." + _ftype.toLocaleLowerCase();
          let imgindex = $.inArray(_ftype_to, image_types);
          let videoindex = $.inArray(_ftype_to, video_types);
          if (filesize > file_size) {
              return alert("文件过大！");
          }
          let chatUsid = foowwLocalStorage.get(chatUsidKey);
          let chatSession = foowwLocalStorage.get(chatSessionKey);
          if (imgindex >= 0) {
              return send_chat_images(
                  clipboardFile,
                  chatUsid,
                  chatSession,
                  filename,
                  filesize
              );
          } else if (videoindex >= 0) {
              return snd_chat_video(
                  clipboardFile,
                  chatUsid,
                  chatSession,
                  filename,
                  filesize
              );
          } else {
              return alert("文件格式错误!~~~~~" + filename);
          }
      }
  });

  // 评论弹窗提交
  $(".subPingLunBtn").on("click", function () {
      let level = $(".pfLevel .icon-pingfen").length;
      let cntText = $.trim($("#pinLunText").val());
      if (level <= 0) {
          return alert("请选择评分等级！");
      }
      if (!cntText) {
          return alert("请输入评论内容！");
      }
      let chatUsid = foowwLocalStorage.get(chatUsidKey);
      let chatSession = foowwLocalStorage.get(chatSessionKey);
      let _data = {
          chatUsid: chatUsid,
          chatSession: chatSession,
          level: level,
          cntText: cntText,
          action: "sub_opl",
      };
      websocket_emit(socket_app, "finishConversation", _data);
  });

  // 监控粘贴板上传图片
  $("#textContent").bind("paste", function (e) {
      // 获取文本值
      // let textl = event.clipboardData.getData('text');
      if (event.clipboardData.files.length <= 0) {
          return;
      }

      let file = event.clipboardData.files[0];
      // 判断类型
      if (!/^image\/[jpeg|png|gif|jpg]/.test(file.type)) {
          return;
      }

      // 读取成base64
      let reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = function (event) {
          $("#diaShade").show();
          $(".dialogWrapDanFu").hide();
          $(".confirmModal").show();
          $(".promptBox").find(".xw").hide();
          let c_img_obj = $(".promptBox").find("img");
          c_img_obj.attr("src", event.target.result);
          c_img_obj.show();
      };
      clipboardFile = file;
  });

  // 问题选择监控
  $("input[type='radio']").on("click", function () {
      let problem = $.trim($("input[name='problem']:checked").val());
      $(".demoIMage img").attr("src", "");
      if (problem === "czwt") {
          $("#account").parent().show();
          $("#czTime").parent().show();
          $("#problemImage").parent().show();
          $("#cjhdText").parent().hide();
          $("#txTme").parent().hide();
      } else if (problem === "txwt") {
          $("#account").parent().show();
          $("#txTme").parent().show();
          $("#problemImage").parent().show();
          $("#cjhdText").parent().hide();
          $("#czTime").parent().hide();
      } else if (problem === "cjsq") {
          $("#account").parent().show();
          $("#cjhdText").parent().css("display", "flex");
          $("#problemImage").parent().hide();
          $("#txTme").parent().hide();
          $("#czTime").parent().hide();
      } else if (problem === "qtwt") {
          $("#account").parent().hide();
          $("#cjhdText").parent().hide();
          $("#problemImage").parent().hide();
          $("#txTme").parent().hide();
          $("#czTime").parent().hide();
          $(".subBtn").hide();
          $(".enterBtn").show();
      }
  });

  
// 提交留言
function sub_LeaveMessage_func() {
    let chatUsid = foowwLocalStorage.get(chatUsidKey);
    if (!chatUsid) {
        alert("页面停留过久，请刷新重试！");
        return location.reload();
    }
    let username = $.trim($("#username").val());
    let telephone = $.trim($("#telephone").val());
    let email = $.trim($("#email").val());
    let note = $.trim($("#note").val());
  
    if (username && username.length > 10) {
        return alert("姓名长度过长！");
    }
    if (note && note.length > 500) {
        return alert("备注长度过长！");
    }
    var reg =
        /^([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+@([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+\.[a-zA-Z]{2,3}$/;
    if (email && !reg.test(email)) {
        return alert("请输入合法的邮箱！");
    }
  
    if (!username) {
        return alert("请输入姓名");
    }
    if (!telephone) {
        return alert("请输入电话");
    }
    if (!note) {
        return alert("请输入备注");
    }
    let pdata = {
        action: "subLeaveMessage",
        username: username,
        telephone: telephone,
        email: email,
        note: note,
        chatUsid: chatUsid,
        site_code: sessionCode,
    };
    websocket_emit(socket_app, "leaveMessage", pdata);
    $(".LeaveMessage").hide();
    alert("您的信息已提交成功！");
    let ttt = setTimeout(function () {}, 3000);
  }
  
  // 评分
  function pf_func(obj) {
    if (obj.hasClass("icon-pingfen1")) {
        obj.removeClass("icon-pingfen1").addClass("icon-pingfen");
    } else {
        obj.removeClass("icon-pingfen").addClass("icon-pingfen1");
    }
  }

  
  // 发送图片
  function send_chat_images(imgfile, chatUsid, chatSession, filename, filesize) {
    let crr_time = new Date();
    let crr_timeC = Date.parse(crr_time);
    let daTime = formatDate(crr_time, "MM-dd hh:mm");
    let uoloadCode = getRandomString(6) + crr_timeC;
    let chatMeassgeObj = $(".chatMeassge");
    let html = "";
    html +=
        '<div class="chat-block chatR">' +
        '<div class="inside">' +
        '<img src="/public/chat/images/user.png" alt="" class="userImage">' +
        '<div class="chatting-right">' +
        '<div class="chat-content chat-content-img" id="' +
        uoloadCode +
        '">' +
        '<img src="/public/chat/images/loading3.gif" alt="" class="loading">' +
        '<a href="" style="display: none;"><img src="" alt=""></a>' +
        '<div class="time" style="display: none;">' +
        daTime +
        "</div>" +
        "</div></div>" +
        "</div></div>";
    chatMeassgeObj.append(html);
    chatMeassgeObj.scrollTop(chatMeassgeObj[0].scrollHeight);
    var formdata = new FormData();
    formdata.append("upload", imgfile);
    formdata.append("action", "chatUploadImage");
    formdata.append("chatUsid", chatUsid);
    formdata.append("chatSession", chatSession);
    formdata.append("filename", filename);
    formdata.append("filesize", filesize);
    xtajax.post({
        data: formdata,
        contentType: false,
        processData: false,
        success: function (data) {
            if (data.code === 200) {
                websocket_emit(socket_app, "chatUploadFile", {
                    image: data.message,
                    chatSession: chatSession,
                    chatUsid: chatUsid,
                    uoloadCode: uoloadCode,
                    action: "upload_image",
                });
            } else {
                $("#" + uoloadCode)
                    .parent()
                    .parent()
                    .parent()
                    .remove();
                return alert(data.message);
            }
        },
    });
  }
  
  // 发送视频
  function snd_chat_video(imgfile, chatUsid, chatSession, filename, filesize) {
    let crr_time = new Date();
    let crr_timeC = Date.parse(crr_time);
    let daTime = formatDate(crr_time, "MM-dd hh:mm");
    let uoloadCode = getRandomString(6) + crr_timeC;
    let chatMeassgeObj = $(".chatMeassge");
    let html = "";
    html +=
        '                    <div class="chat-block chatR">' +
        '                        <div class="inside">' +
        '                            <img src="/public/chat/images/user.png" alt="" class="userImage">' +
        '                            <div class="chatting-right" id="' +
        uoloadCode +
        '">' +
        '                                <div class="chat-content">' +
        '                                    <div class="chatFile">' +
        '                                        <div style="position: relative; height: 70px; overflow: hidden;">\n' +
        '                                            <i class="iconfont icon-shipin2" style="font-size: 39px; line-height: 75px;"></i>\n' +
        "                                        </div>\n" +
        '                                        <div style="position: relative; display: flex; flex-direction: column; justify-content: flex-start; font-size: 13px; line-height: 20px; margin-left: 15px; color: #FFFFFF;">\n' +
        '                                            <div style="margin-bottom: 3px; position: relative;white-space: nowrap;overflow: hidden;text-overflow: ellipsis;max-width: 100px;">' +
        filename +
        "</div>\n" +
        '                                            <div style="position: relative; display: flex;">' +
        filesize +
        'B<time class="time" style="vertical-align: -2px; margin-left: 40px; top: 1px;">' +
        daTime +
        "</time></div>\n" +
        "                                        </div>\n" +
        "                                    </div>\n" +
        '                                    <div class="progress" style="height: 5px;">\n' +
        '<div class="progress-bar progress-bar-striped" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%;"></div>' +
        "                                    </div>\n" +
        "                                </div>\n" +
        "                            </div>\n" +
        "                        </div>\n" +
        "                    </div>";
    chatMeassgeObj.append(html);
    chatMeassgeObj.scrollTop(chatMeassgeObj[0].scrollHeight);
  
    var send_showprogress = function (evt) {
        var loaded = evt.loaded;
        var tot = evt.total;
        var percent = Math.floor((100 * loaded) / tot);
        var progressbar = $("#" + uoloadCode + " .progress-bar");
        // progressbar.html(percent+'%');
        // progressbar.attr('aria-valuenow',percent);
        progressbar.css("width", percent + "%");
    };
  
    var send_hideprogressbar = function () {
        var progressbar = $("#" + uoloadCode).find(".progress");
        progressbar.html("0%");
        progressbar.attr("aria-valuenow", 0);
        progressbar.css("width", "0%");
        progressbar.remove();
    };
  
    var formdata = new FormData();
    formdata.append("upload", imgfile);
    formdata.append("action", "chatUploadVideo");
    formdata.append("chatUsid", chatUsid);
    formdata.append("chatSession", chatSession);
    formdata.append("filename", filename);
    formdata.append("filesize", filesize);
    xtajax.post({
        data: formdata,
        contentType: false,
        processData: false,
        progress: send_showprogress,
        success: function (data) {
            if (data.code === 200) {
                websocket_emit(socket_app, "chatUploadFile", {
                    video: data.message,
                    chatSession: chatSession,
                    chatUsid: chatUsid,
                    uoloadCode: uoloadCode,
                    action: "upload_video",
                    filename: filename,
                    filesize: filesize,
                });
                let ssst = setTimeout(function () {
                    send_hideprogressbar();
                }, 1000);
            } else {
                $("#" + uoloadCode)
                    .parent()
                    .parent()
                    .parent()
                    .remove();
                return alert(data.message);
            }
        },
    });
  }  
});
