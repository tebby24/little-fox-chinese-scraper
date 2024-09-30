
var G_OPENWINDOW = false;
var movie_fc_id = "";
var movie_fc_id_free = "";

function _script_popup(pop_id,popSizeW,popSizeH) {
	if(screen.height < popSizeH){ popSizeH = (screen.height- 80);}
	if(screen.width < popSizeW){ popSizeW = (screen.width- 80);}

	vtop = ((screen.height - popSizeH)-120) / 2;
	vleft = ((screen.width - popSizeW)-100) / 2;

	Player.windowpop_id=window.open("/static/blank.html?4", pop_id, 'width='+popSizeW+'px,height='+popSizeH+'px,top='+vtop+',left='+vleft+',resizable=1,copyhistory=0,toolbar=0,location=0,directories=0,menubar=0,status=yes,toolbar=no');

	Player.windowpop_id.document.open("text/html");
	Player.windowpop_id.document.writeln("<html xmlns='http://www.w3.org/1999/xhtml' xml:lang='ko'>");
	Player.windowpop_id.document.writeln("<body style='margin:0px;'>");
	Player.windowpop_id.document.writeln("<script>");
	Player.windowpop_id.document.writeln("	 window.onload=function(){");
	Player.windowpop_id.document.writeln("		try");
	Player.windowpop_id.document.writeln("		{");
	Player.windowpop_id.document.writeln("			window.opener.G_OPENWINDOW = 1;");
	Player.windowpop_id.document.writeln("		}");
	Player.windowpop_id.document.writeln("		catch (e)");
	Player.windowpop_id.document.writeln("		{");
	Player.windowpop_id.document.writeln("		}");
	Player.windowpop_id.document.writeln("	}");
	Player.windowpop_id.document.writeln("</script>");
	Player.windowpop_id.document.writeln("</body>");
	Player.windowpop_id.document.writeln("</html>");

	Player.windowpop_id.document.close();
	Player.windowpop_id.focus();

}

var Player =
	{
		// ì „ì²´ì°½ ê¸°ë³¸SizeëŠ” 700x528 (FlashPlayerì™€ ActiveXPlayer(700x530)ê°€ ì°½í¬ê¸° ì„œë¡œ ë‹¤ë¥´ì§€ë§Œ ê·¸ëƒ¥ í†µì¼í•´ì„œ ì‚¬ìš©í•¨)
		// ì»¨íŠ¸ë¡¤ë°” ëº€ ìˆœìˆ˜ ë™í™” SizeëŠ” 700x500
		// width : 700, height : 528,
		width : 800, height : 570,
		g_nType : 0,
		g_sCid : '',
		g_sAuth: '',
		g_sFree: '',
		g_bPass: false,
		windowpop_id: null,
		t_play_fc_id: null,
		t_play_data: null,
		objTimer: null,

		delay_post : function() {

			if( G_OPENWINDOW != 1 || Player.windowpop_id==null) {
				Player.objTimer = window.setTimeout( function() { Player.delay_post() }, 700);
				return;
			}

			var data = Player.t_play_data;

			if(data)
			{
				this.type = data.content;
				this.free = data.free=="F" ? data.free : "";

				if( this.type=="G" ){		// ê²Œìž„
					Player.game(Player.t_play_fc_id, this.free);

				} else {
					var _tracks = Player.t_play_fc_id;
					var _types = this.type;
					var _free = this.free;
					var _ptype = 'p';

					Player.g_bPass = false;

					// ì´ì–´ë“£ê¸°
					if( !_tracks ){
						_tracks = document.getElementById("play_list").value;
						_types = document.getElementById("type_list").value;
						_ptype = "t";
					}

					// ë¬´ë£Œ - ìœ ë£Œ
					if( _free == "F" ) Player.popup_post(_tracks,_types,_ptype, _free, 1);
					else Player.popup_post(_tracks,_types,_ptype,_free);

				}
			}
		},
		popup_post : function(tracks,types,ptype,free, f_type)
		{
			var action_url = ROOT_PATH+"/player/relay";

			// ë¬´ë£Œ url
			if(f_type==1){
				action_url = ROOT_PATH+"/player/relay_free/";
			}

			var free = free || 'N';
			if( free == "null" ) return;
//console.log( free );
			if ( free != 'F' ) {
//console.log( Login.need() );
				// if ( Login.need() === false ) {return;}
			}

			/*
                ëª¨ë‹ˆí„° ì‚¬ì´ì¦ˆ ë³„ ë™í™”íŒì—…ì°½ ìžë™ ì¡°ì ˆ
            */
			if(FxUserDef.popSize() == 0) {
				/*
                    í™•ëŒ€ ë°°ìˆ˜ ê³„ì‚° ë¡œì§
                */
				if ((screen.height > 399 && screen.height < 2000)
					&& (screen.width > 399 && screen.width < 3000)){
					if (screen.height < screen.width)
						popSizeX = screen.height / this.height * 0.75;
					else
						popSizeX = screen.width / this.width * 0.75;
				}
				else {
					popSizeX = 1;
				}
			}
			else {
				popSizeX = FxUserDef.popSize();
			}

			popSizeW = Math.round(this.width * popSizeX);
			popSizeH = Math.round(this.height * popSizeX);



			var form = document.createElement("form");
			var trackField = document.createElement("input")
			trackField.setAttribute("type","hidden");
			trackField.setAttribute("name","tracks");
			trackField.setAttribute("value",tracks);
			form.appendChild(trackField);
			var typeField = document.createElement("input")
			typeField.setAttribute("type","hidden");
			typeField.setAttribute("name","types");
			typeField.setAttribute("value",types);
			form.appendChild(typeField);
			var ptypeField = document.createElement("input")
			ptypeField.setAttribute("type","hidden");
			ptypeField.setAttribute("name","ptype");
			ptypeField.setAttribute("value",ptype);
			form.appendChild(ptypeField);
			var freeField = document.createElement("input")
			freeField.setAttribute("type","hidden");
			freeField.setAttribute("name","free");
			freeField.setAttribute("value",free);
			form.appendChild(freeField);
			document.body.appendChild(form);

			form.method = "post";
			form.target = "ChinesePlayer";
			form.action = action_url;
			form.submit();
		},



		popup : function ( url, free )
		{
			var free = free || 'N';
			if( free == "null" ) return;

			if ( free != 'F' ) {
				if ( Login.need() === false ) {return;}
			}

			/*
                ëª¨ë‹ˆí„° ì‚¬ì´ì¦ˆ ë³„ ë™í™”íŒì—…ì°½ ìžë™ ì¡°ì ˆ
            */
			if(FxUserDef.popSize() == 0) {
				/*
                    í™•ëŒ€ ë°°ìˆ˜ ê³„ì‚° ë¡œì§
                */
				if ((screen.height > 399 && screen.height < 2000)
					&& (screen.width > 399 && screen.width < 3000)){
					if (screen.height < screen.width)
						popSizeX = screen.height / this.height * 0.75;
					else
						popSizeX = screen.width / this.width * 0.75;
				}
				else {
					popSizeX = 1;
				}
			}
			else {
				popSizeX = FxUserDef.popSize();
			}

			popSizeW = Math.round(this.width * popSizeX);
			popSizeH = Math.round(this.height * popSizeX);

			var popup = _popup( url , 'ChinesePlayer' , popSizeW , popSizeH, '' , '' , '' , 1 );
			return true;
		},

		open_game : function ( fc_id , ptype , free )
		{
			var ptype = ptype || 'p';
			var free = free || 'N';

			var url = ROOT_PATH+'/player/loadgame/' + fc_id ;
			Player.popup ( url , free );
		},

		open : function ( fc_id , ptype , free , auth)
		{
			var free = free || 'N';
			var type = "";
			var chk_url = ROOT_PATH+'/player/getChk_ajax/'+fc_id;
			$.ajax({
				type:'post',
				url:chk_url,
				success:function(data){
					var req = eval('('+transport.responseText+')');
					this.type = req.content;
					this.free = req.free=="Y" ? "F" : "N";

					var url = ROOT_PATH+'/player/view/' + fc_id + '/' + this.type + '/' + free;
					Player.popup ( url );
				},
				error:function(){
					alert ('unable to load...please try again.');
				}

			});
		},

		// ì´ì–´ë“£ê¸°
		title : function ( fc_id , auth )
		{
			this.open ( fc_id , 'p' , '' , auth );
			Player.g_bPass = false;
		},

		//-- bfox ë™í™”,ë™ìš” ì°½ ë„ìš°ê¸°
		view : function (fc_id, free, no_caption)
		{
			var LANG_FLAG = window.location.pathname.split('/');
			var html = '';

			if(LANG_FLAG[1] == 'en')
			{
				html += '<div id="layerFlashStop" class="layer_wrap flash_stop" style="display:block;">';
				html += '	<div class="layer_content">';
				html += '		<div class="cont">';
				html += '			<p class="message1">';
				html += '				<strong>Please Update Your Browser</strong>';
				html += '				<br>Little Fox has discontinued';
				html += '				<br>using Adobe Flash.';
				html += '			</p>';
				html += '			<p class="message2"> Please update to a browser that supports HTML5 <br>to continue using Little Fox.</p>';
				html += '			<a class="btn_detail" href="https://chinese.littlefox.com/en/board/view?id=news&seq=3301&page=">View Details</a>';
				html += '		</div>';
				html += '		<div class="btn">';
				html += '			<button type="button" onclick="Player.flashClose();">Close</button>';
				html += '		</div>';
				html += '	</div>';
				html += '</div>';
			}

			movie_fc_id = fc_id;
			movie_fc_id_free = free;

			if(typeof(free)=="undefined") free="";
			if(typeof(no_caption)=="undefined") no_caption="N";

			// HTML5 í”Œë ˆì´ì–´ê°€ ê°€ëŠ¥í•˜ë©´ ë¶„ê¸°
			if (PlayerH5.enableCheck() || BROWSER === 'Edge')
			{
				PlayerH5.popup(fc_id);
				return false;
			}
			else {
				//2020.11.09 Flash ì¤‘ë‹¨
				if (this.checkDiffDate('2020-11-09')) {
					if ($('#layerFlashStop').length > 0) {
						return;
					} else {
						$('body').append(html);
						return;
					}
				}
			}

			/*
                ëª¨ë‹ˆí„° ì‚¬ì´ì¦ˆ ë³„ ë™í™”íŒì—…ì°½ ìžë™ ì¡°ì ˆ
            */
			if(FxUserDef.popSize() == 0) {
				/*
                    í™•ëŒ€ ë°°ìˆ˜ ê³„ì‚° ë¡œì§
                */
				if ((screen.height > 399 && screen.height < 2000)
					&& (screen.width > 399 && screen.width < 3000)){
					if (screen.height < screen.width)
						popSizeX = screen.height / this.height * 0.75;
					else
						popSizeX = screen.width / this.width * 0.75;
				}
				else {
					popSizeX = 1;
				}
			}
			else {
				popSizeX = FxUserDef.popSize();
			}
			popSizeW = Math.round(this.width * popSizeX);
			popSizeH = Math.round(this.height * popSizeX);

			Player.windowpop_id=null;
			Player.objTimer=null;

			try
			{
				G_OPENWINDOW = true;
				//	if( free=="F" ) {
				G_OPENWINDOW = false;
				_script_popup('ChinesePlayer' , popSizeW , popSizeH);
				//	}

				//	if(Cookie.get('cx0') && ( Cookie.get('cx5')=="UA" || Cookie.get('cx5')=="UR" ) ) {
				//		G_OPENWINDOW = false;
				//		_script_popup('player' , popSizeW , popSizeH);
				//	}

				//	if( G_OPENWINDOW==true && free=="") {
//
//				if ( Login.need() === false ) {
//					return;
//				}
//			}
			}
			catch (e)
			{
			}

			if( free=="Y" ) {

				// if ( Login.need() === false ) {
				// 	return;
				// }
				/*
                && Login.need() == false) {

                if(Cookie.get('cx0')) {
                    Login.needSubscribe();
                } else {
                    Login.needPop();
                }*/
			}

			if( Player.windowpop_id == null ) {
				//alert("popup Disabled..");
			}

			var type = "";
			var free = "";
			var chk_url = ROOT_PATH+'/player/chk_free/'+fc_id;

			$.ajax({
				type:'post',
				url:chk_url,
				dataType:'json',
				data:"fc_id="+fc_id,
				async:true,
				success:function(data){
					Player.t_play_fc_id = fc_id;
					Player.t_play_data = data;

					Player.delay_post();
				},
				error:function(){
					alert ('unable to load...please try again.');
				}

			});
		},


		//-- ê²Œìž„ ì°½ ë„ìš°ê¸°
		game : function ( fc_id , free )
		{
			this.open_game ( fc_id , 'p' , free );		// ì „ë¶€ë‹¤ bfox
		},


		efoxrelay : function (free){
			if(!this.popup ( '', free )) {return;}

			var tracks		= document.getElementById("play_list").value;
			var types		= document.getElementById("type_list").value;
			var play_track	= tracks.split(':');
			var play_type	= types.split(':');
			//alert(play_track[0]+'---');

			Player.g_bPass = false;;

			if( FxUserDef.selPlayer() == 'F' )
			{
				var url		= '';
				if( free == 'F' ){
					url = ROOT_PATH+'/player/efoxrelay_free/';
				}else{
					url = ROOT_PATH+'/player/efoxrelay/';
				}
				Player.popup ( url, free );
			}
			else
			{
				Cookie.set ( 'track_list' , tracks );
				Cookie.set ( 'track_type',  types );
				Player.popup ( '/static/old_player/FPplay.foxp', free );
			}
		},

		relay : function (free,tracks,types,ptype)
		{
			var _types = types;
			var _tracks = tracks;
			var _ptype = ptype;

			Player.g_bPass = false;;

			// ì´ì–´ë“£ê¸°
			if( !tracks ){
				_tracks = document.getElementById("play_list").value;
				_types = document.getElementById("type_list").value;
				_ptype = "t";
			}


			if( free == "F" ){		// ë¬´ë£Œ
				Player.popup_post(_tracks,_types,_ptype,free, 1);
			}
			else{		// ìœ ë£Œ
				Player.popup_post(_tracks,_types,_ptype,free);
			}
		},

		//-- í”Œë ˆì´ì–´ì—ì„œ í˜¸ì¶œ
		trackNextNo : function ( no )
		{
			var ck_track_list = Cookie.get ('track_list');
			var split_ck_track_list = ck_track_list.split(':');

			var track_size = split_ck_track_list.size();
			var next_no = no % track_size;

			//return split_ck_track_list[next_no];
			this.thisMovie("foxP").sendNextID(split_ck_track_list[next_no]);
		},

		//-- í”Œë ˆì´ì–´ì—ì„œ í˜¸ì¶œ
		thisMovie : function (movieName)
		{
			if (navigator.appName.indexOf("Microsoft") != -1) {
				return window[movieName];
			} else {
				return document[movieName];
			}
		},

		//-- í”Œëž˜ì‹œ í”Œë ˆì´ì–´ ë²„ì „ ì—…ë°ì´íŠ¸ ê³µì§€ì°½ì—ì„œ ì—…ë°ì´íŠ¸ íŽ˜ì´ì§€ë¡œ ì´ë™í•˜ì§€ ì•Šê³ , ë‹¤ìŒì— ì—…ë°ì´íŠ¸ë¥¼ í´ë¦­í–ˆì„ ê²½ìš° ì²˜ë¦¬ (added by yjpark, 2011.07.12)
		updateLater : function ()
		{
			Player.g_bPass = true;

			switch(Player.g_nType){
				case 1:		Player.title(Player.g_sCid, Player.g_sAuth);
					break;

				case 2:		Player.view(Player.g_sCid, Player.g_sFree);
					break;

				case 3:		Player.relay('');
					break;

				default:	break;
			}
		},

		checkDiffDate : function(standardDay)
		{
			var date = new Date();
			var today = date.getFullYear() + '-' + ("0"+(date.getMonth()+1)).slice(-2) + '-' + ("0"+date.getDate()).slice(-2);
			today = today.split('-');
			standardDay = standardDay.split('-');

			var todayCompare = new Date(today[0], parseInt(today[1])-1, today[2]);
			var stanCompare = new Date(standardDay[0], parseInt(standardDay[1])-1, standardDay[2]);

			if(todayCompare.getTime() >= stanCompare.getTime())
			{
				return true;
			}
			else
			{
				return false;
			}
		},

		flashClose : function ()
		{
			$('#layerFlashStop').remove();
		}
	};
