if exists("g:mrglab_plugin_loaded")
    finish
endif
let g:mrglab_plugin_loaded = 1


" --------------------------------
python3 << EOF
import sys
import vim
sys.path.append(vim.eval('expand("<sfile>:h")') + "/../python/")
import vim_mrglab
EOF


" --------------------------------
"  Function(s)
" --------------------------------
function! mrglab#InitMrGlab()
    "command LoadMrGlab call rboard#LoadReviewBoard()
    python3 vim_mrglab.init_vim()
    "map <leader>lr :LoadReviewBoard<CR>
endfunction

"function! s:MakeComment() range
"python rboard.action_make_comment()
"endfunction
"
"function! s:SaveComment() range
"python rboard.action_save_comment()
"endfunction
"
"function! s:LoadDiff()
"python rboard.action_view_diff()
"endfunction
"
"function! s:TabClose()
"python rboard.action_kill_tab()
"endfunction
"
"function! s:ViewRequest()
"python rboard.action_view_request()
"endfunction
"
"function! s:MoveDown(arg)
"python rboard.action_move_down(vim.eval("a:arg"))
"endfunction
"
"function! s:EditBody(arg)
"python rboard.action_edit_body(vim.eval("a:arg"))
"endfunction
"
"function! s:SubmitReview()
"python rboard.action_submit_review()
"endfunction
"
"function! s:SaveBody(arg)
"python rboard.action_save_body(vim.eval("a:arg"))
"endfunction
"
"function! s:ViewDraftReview()
"python rboard.action_view_draft_review()
"endfunction
"
"function! s:LoadMore(arg)
"python rboard.action_load_more_reviews(vim.eval("a:arg"))
"endfunction
"
"
"function! rboard#LoadReviewBoard()
"python rboard.action_load_reviews()
"endfunction
"
"" --------------------------------
""  Expose our commands to the user
"" --------------------------------
call mrglab#InitMrGlab()
