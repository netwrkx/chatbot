touch AUTOLOG
pwd > AUTOLOG
date >> AUTOLOG
whoami >> AUTOLOG
np=`ps -aux | grep dialoggptBot | wc -l`
echo $np >> AUTOLOG
if [[ "$np" != "2" ]]
then
	echo "Restarting chatbot..."
	pkill -9 -f dialoggptBot
	sleep 15s
	nohup /home/lawrence/anaconda3/bin/python /home/lawrence/chatbot/dialoggptBot.py > /dev/null 2>&1
	echo "Done"
fi

