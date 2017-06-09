# Add back sbin dirs to unprivileged users PATH
case $PATH in
	*/sbin/*) ;;
	*) PATH=/usr/local/sbin:/usr/sbin:/sbin:$PATH ;;
esac
