-- osascript analytics/send_report.applescript <to> <subject> <body.txt> <attachment.pdf>
-- Sends from Ryan's Gmail account in Apple Mail, with the PDF attached from disk.
on run argv
	set {toAddr, subj, bodyPath, pdfPath} to argv
	set bodyText to read (POSIX file bodyPath) as «class utf8»
	tell application "Mail"
		set msg to make new outgoing message with properties {subject:subj, content:bodyText & return & return, sender:"Ryan Delahunt <rdelahunt1@gmail.com>", visible:true}
		tell msg
			make new to recipient at end of to recipients with properties {address:toAddr}
			make new attachment with properties {file name:(POSIX file pdfPath) as alias} at after the last character of content
		end tell
		delay 3
		send msg
	end tell
	return "sent to " & toAddr
end run
