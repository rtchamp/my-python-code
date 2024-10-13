# Java의 ClassLoader 가져오기
set classLoader [java::call ClassLoader getSystemClassLoader]

# 모든 리소스 가져오기
set resources [$classLoader getResources ""]

# 패키지 목록을 저장할 집합 생성
set packages [java::new java.util.HashSet]

# 모든 리소스 순회
while {[$resources hasMoreElements]} {
    set url [$resources nextElement]
    set path [$url getPath]
    
    # JAR 파일 처리
    if {[string match "*.jar" $path]} {
        set jarFile [java::new java.util.jar.JarFile $path]
        set entries [$jarFile entries]
        
        while {[$entries hasMoreElements]} {
            set entry [$entries nextElement]
            set name [$entry getName]
            
            if {[string match "*.class" $name]} {
                set className [string map {".class" "" "/" "."} $name]
                if {[string first "." $className] != -1} {
                    set packageName [string range $className 0 [string last "." $className]-1]
                    $packages add $packageName
                }
            }
        }
        
        $jarFile close
    }
}

# 패키지 목록 출력
set iterator [$packages iterator]
while {[$iterator hasNext]} {
    puts [$iterator next]
}