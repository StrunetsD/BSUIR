#include <iostream>
#include <vector>
#include <sstream>
#include <unistd.h>
#include <sys/wait.h>
#include <string.h>

using namespace std;

vector<char*> symbols(const string& row){
    vector<char*> args;
    istringstream iss(row);
    // почитай об этом потоке(типа класс istringstream,тут просто говорится,
    //что строка превращается в поток   )
    string token;
    while(iss >> token){ // чтение данных из поткоа
        char* arg = new char[token.size()+1];
        strcpy(arg,token.c_str());
        args.push_back(arg);
    }
    args.push_back(nullptr);// это необходимо для execvp()
    return args;
}

int main(){
    string cmd;
    
    while(true){
        cout<<"MyShell>";
        if(!getline(cin,cmd)){
            cout<<"something wrong";
            exit(0);
        }
        if(cmd == "exit"){
            exit(0);
        }
        //для cd отдельно пришлось делать, хз, почему оно не работало без этого блока

        if(cmd.substr(0,2)=="cd"){
            string path = cmd.substr(3);
            if(chdir(path.c_str())!=0){// c_str -- превращает строку в массив char 
                cout<<"no such path"<<"\n";
            }
        }
        vector<char*> test = symbols(cmd);
        pid_t ret = fork();// new child procces
        if(ret < 0){
            cout<<"error";
        }
        if(ret == 0){
            if(execvp(test[0], &test[0]) == -1){
                // execvp -- замена текущего процесса (дочернего) на указанный процесс(блок кода) 
                //test[0] -- command
                //&test[0] -- указывает на вектор аргументов 
                exit(0);
            }
        }
        else
            {
                int status;
                waitpid(ret,&status,0);
                //ожидает завершение child процесса
                //ret -- идентификатор процесса (PID), для которого ты хочешь ожидать завершения
                //&status -- записывается статус
                // 0 - флаг, определяющий поведение функции(в методе про это WNOHANG и пр)
            }
        
        for(char* arg : test){
            delete [] arg;
        }
        
    }
}

