# Triển khai trên K8s


- Tạo Cluster (`kind-config`)
```
kind create cluster --config kind-config.yaml
```
- Verify
```
kubectl cluster-info
kubectl get nodes -o wide
```

NAME|                            STATUS|   ROLES|           AGE|
| --- | --- | --- | --- |
ecommerce-local-control-plane|  Ready|    control-plane|   ...|
ecommerce-local-worker  |       Ready|   &lt;none&gt; |         ...|
ecommerce-local-worker2 |       Ready|   &lt;none&gt;|          ...|

# `Môi trường lab hiện tại cần postgresql chạy local`
Sau khi namespace xong, sẽ triển khai PostgreSQL vào overlays/local/, đúng với kiến trúc đã thống nhất: PostgreSQL chỉ tồn tại ở local Kind; production sau này sẽ dùng PostgreSQL bên ngoài cluster.

## Tạo namespcae `ecommerce` (`namespace.yaml`)

- Apply the namespcae
```
kubectl apply -f base/namespace.yaml
```

- Verify
```
kubectl get namespaces
```
- Kết quả đầu ra mong muốn
Phải thấy `ecommerce` trong Field NAME

NAME|                 STATUS|   AGE|
| --- | --- | --- |
default|              Active|   3m53s|...|
ecommerce|            Active|  5s|...|
kube-node-lease|      Active|   3m53s|...|
kube-public|          Active|   3m53s|...|
kube-system |         Active|  3m53s|...|
local-path-storage|   Active|   3m50s|...|

- Deploy PostgreSQL (`postgres.yaml`)

```
kubectl apply -f k8s/overlays/local/postgres.yaml
```
## Pod 
Pod là đơn vị tính toán điện toán nhỏ nhất có thể triển khai và quản lý trong k8s
Một pod là một nhóm có  nhiều hoặc 1 container ở cùng với nhau. Với tất cả tài nguyên dùng chung với nhau (network, shared storage). Một Pod mô phỏng một "máy chủ logic" dành riêng cho ứng dụng: nó chứa một hoặc nhiều container ứng dụng được liên kết tương đối chặt chẽ. Trong các ngữ cảnh không phải điện toán đám mây, các ứng dụng được thực thi trên cùng một máy vật lý hoặc máy ảo tương tự như các ứng dụng đám mây được thực thi trên cùng một máy chủ logic.

Ngoài các vùng chứa ứng dụng, một Pod có thể chứa... khởi tạo containerNhững đoạn mã này chạy trong quá trình khởi động Pod. Bạn cũng có thể chèn chúng. thùng chứa tạm thời Để gỡ lỗi một Pod đang chạy.

Trong cụm Kubernetes, Pod được sử dụng theo hai cách chính:

Các Pod chạy một container duy nhất . Mô hình "một container trên mỗi Pod" là trường hợp sử dụng Kubernetes phổ biến nhất; trong trường hợp này, bạn có thể coi Pod như một lớp bao bọc xung quanh một container duy nhất; Kubernetes quản lý các Pod chứ không phải quản lý trực tiếp các container.

Pod là các module chạy nhiều container cần hoạt động cùng nhau . Một Pod có thể bao gồm một ứng dụng gồm nhiều container đặt cùng vị trí , liên kết chặt chẽ và cần chia sẻ tài nguyên. Các container đặt cùng vị trí này tạo thành một đơn vị thống nhất.

Việc nhóm nhiều container cùng vị trí và cùng được quản lý vào một Pod duy nhất là một trường hợp sử dụng tương đối nâng cao. Bạn chỉ nên sử dụng mô hình này trong những trường hợp cụ thể khi các container của bạn có mối liên hệ chặt chẽ với nhau.

- Đợi vài giây để quá trình tạo hoàn thành mới chạy để verify.
```
kubectl get pods -n ecommerce 
```
- Đầu ra mong muốn:
postgres-xxxxxxxxxx   0/1   ContainerCreating

## Service trong k8s

`Service trong Kubernetes là một lớp trừu tượng định nghĩa một tập hợp logic các Pod và cho phép công khai lưu lượng truy cập, cân bằng tải và service discovery cho những Pod đó.`

Service trong Kubernetes là một lớp trừu tượng định nghĩa một tập hợp logic các Pod và chính sách truy cập cho chúng. Service cho phép các Pod phụ thuộc nhau có thể kết nối với nhau một cách "lỏng lẻo". Service được định nghĩa bằng YAML hoặc JSON, giống như tất cả các manifest đối tượng khác của Kubernetes. Tập hợp các Pod mà Service nhắm đến thường được xác định bằng một label selector (xem phần dưới để hiểu tại sao đôi khi bạn có thể muốn một Service mà không cần selector trong đặc tả).

Mặc dù mỗi Pod có một địa chỉ IP duy nhất, những IP này không được công khai ra bên ngoài cluster nếu không có Service. Service cho phép ứng dụng của bạn nhận lưu lượng truy cập từ bên ngoài. Service có thể được công khai theo nhiều cách khác nhau bằng cách chỉ định type trong phần spec của Service:

- ClusterIP (mặc định) - Công khai Service trên một IP nội bộ trong cluster. Kiểu này chỉ cho phép Service có thể truy cập được từ bên trong cluster.

- NodePort - Công khai Service trên cùng một port của mỗi Node được chọn trong cluster sử dụng NAT. Cho phép Service có thể truy cập được từ bên ngoài cluster thông qua <NodeIP>:<NodePort>. Là tập mở rộng của ClusterIP.

- LoadBalancer - Tạo một bộ cân bằng tải bên ngoài trong cloud hiện tại (nếu được hỗ trợ) và gán một IP cố định bên ngoài cho Service. Là tập mở rộng của NodePort.

- ExternalName - Ánh xạ Service với nội dung của trường externalName (ví dụ: foo.bar.example.com), bằng cách trả về một bản ghi CNAME với giá trị tương ứng. Không thiết lập bất kỳ proxy nào. Kiểu này yêu cầu phiên bản v1.7 trở lên của kube-dns hoặc CoreDNS phiên bản 0.0.8 trở lên.
- Verify
```
kubectl get svc -n ecommerce
```

NAME|                        READY|   STATUS|    RESTARTS|   AGE|
| --- | --- | --- | --- | --- |
postgres-xxxxxxxxxx|        1/1|     Running|   0|          ...|

## Persistent Volumes

Việc quản lý lưu trữ là một vấn đề khác biệt so với việc quản lý các thực thể tính toán (compute instances). Hệ thống con PersistentVolume cung cấp một API cho người dùng và quản trị viên, giúp tách biệt các chi tiết về cách cung cấp lưu trữ khỏi cách thức lưu trữ đó được sử dụng. Để thực hiện điều này, chúng tôi giới thiệu hai tài nguyên API mới: PersistentVolume và PersistentVolumeClaim.

PersistentVolume (PV) là một phần tài nguyên lưu trữ trong cụm (cluster), được quản trị viên cung cấp sẵn hoặc được cấp phát động thông qua các Storage Class. Đây là một tài nguyên trong cụm, tương tự như cách một node được coi là tài nguyên của cụm. Các PV đóng vai trò như các plugin lưu trữ (volume plugins), nhưng có vòng đời độc lập với bất kỳ Pod cụ thể nào sử dụng chúng. Đối tượng API này lưu trữ các chi tiết về cách thức triển khai lưu trữ, chẳng hạn như NFS, iSCSI hoặc hệ thống lưu trữ từ một nhà cung cấp dịch vụ đám mây cụ thể.

PersistentVolumeClaim (PVC) là yêu cầu về lưu trữ từ phía người dùng. Khái niệm này tương tự như Pod: nếu Pod tiêu thụ tài nguyên của node, thì PVC tiêu thụ tài nguyên của PV. Pod có thể yêu cầu các mức tài nguyên cụ thể (như CPU ​​và bộ nhớ), trong khi các PVC có thể yêu cầu dung lượng và các chế độ truy cập (access modes) cụ thể (ví dụ: có thể được gắn kết ở các chế độ như ReadWriteOnce, ReadOnlyMany, ReadWriteMany hoặc ReadWriteOncePod; xem thêm tại mục AccessModes).

Mặc dù PersistentVolumeClaim cho phép người dùng sử dụng các tài nguyên lưu trữ trừu tượng, nhưng trong thực tế, người dùng thường cần các PersistentVolume với những đặc tính khác nhau (ví dụ: về hiệu năng) để giải quyết các vấn đề khác nhau. Các quản trị viên cụm cần có khả năng cung cấp nhiều loại PersistentVolume đa dạng—không chỉ khác biệt về dung lượng hay chế độ truy cập—mà không cần để người dùng phải biết các chi tiết kỹ thuật về cách thức triển khai những tài nguyên lưu trữ đó. Để đáp ứng nhu cầu này, tài nguyên StorageClass đã được ra đời. [Reference](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)

- Verify
```
kubectl get pvc -n ecommerce
```

- Kết quả mong muốn

NAME|           STATUS|   VOLUME|
| --- | --- | --- |
postgres-pvc|   Bound|    ...|

- Xem Events của Pod & deployment status
```
kubectl describe pod postgres-fcdbb969c-nw6h6 -n ecommerce
kubectl get deployment -n ecommerce
```
- Kiểm tra node
```
kubectl get nodes 
```

# ConfigMap + Secret

## ConfigMap


ConfigMap là một đối tượng API được sử dụng để lưu trữ dữ liệu không nhạy cảm dưới dạng các cặp khóa-giá trị (key-value). Các Pod có thể sử dụng ConfigMap thông qua biến môi trường, đối số dòng lệnh hoặc dưới dạng các tệp cấu hình nằm trong một volume.

ConfigMap cho phép bạn tách biệt cấu hình dành riêng cho từng môi trường ra khỏi các image container, nhờ đó giúp các ứng dụng của bạn có tính linh hoạt và dễ dàng di chuyển giữa các môi trường khác nhau. [Reference](https://kubernetes.io/docs/concepts/configuration/configmap/)
- Áp dụng config

```
kubectl apply -f k8s/base/configmap.yaml
```
## Secret
Secret là một đối tượng chứa một lượng nhỏ dữ liệu nhạy cảm, chẳng hạn như mật khẩu, mã thông báo (token) hoặc khóa (key). Thông thường, những thông tin này có thể bị đặt trực tiếp trong đặc tả (specification) của Pod hoặc trong hình ảnh container (container image). Việc sử dụng Secret giúp bạn không cần phải đưa dữ liệu bảo mật vào mã nguồn ứng dụng của mình.

Vì các Secret có thể được tạo độc lập với các Pod sử dụng chúng, nên rủi ro để lộ Secret (cùng với dữ liệu bên trong) trong quá trình tạo, xem hoặc chỉnh sửa Pod sẽ giảm đi. Kubernetes và các ứng dụng chạy trong cụm (cluster) của bạn cũng có thể áp dụng các biện pháp phòng ngừa bổ sung đối với Secret, chẳng hạn như tránh ghi dữ liệu nhạy cảm vào bộ lưu trữ không bay hơi (nonvolatile storage).

Secret có đặc điểm tương tự như ConfigMap, nhưng được thiết kế chuyên biệt để lưu trữ dữ liệu bảo mật. [Reference](https://kubernetes.io/docs/concepts/configuration/secret/)

- Áp dụng cấu hình
```
kubectl apply -f k8s/overlays/local/secret.yaml
```
- Verify 

```
kubectl get secret -n ecommerce
```

# Cấu hình cho các service (Deployment, Kustomization, Service)

[`Deployment`](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) quản lý một tập hợp các Pod để chạy khối lượng công việc của ứng dụng, thường là các ứng dụng không duy trì trạng thái (stateless).
Deployment cung cấp cơ chế cập nhật theo phương thức khai báo (declarative updates) cho các Pod và ReplicaSet.

Bạn mô tả trạng thái mong muốn trong một Deployment, và Deployment Controller sẽ điều chỉnh trạng thái thực tế sao cho khớp với trạng thái mong muốn đó theo một tốc độ được kiểm soát. Bạn có thể thiết lập các Deployment để tạo mới các ReplicaSet, hoặc loại bỏ các Deployment hiện có và tiếp quản toàn bộ tài nguyên của chúng thông qua các Deployment mới. 

[`Kustomization`](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/)là một công cụ dùng để tùy chỉnh các cấu hình Kubernetes. Công cụ này cung cấp các tính năng sau để quản lý các tệp cấu hình ứng dụng:

- tạo tài nguyên từ các nguồn khác nhau
- thiết lập các trường chung (cross-cutting fields) cho các tài nguyên
- kết hợp và tùy chỉnh các tập hợp tài nguyên
- Tạo tài nguyên
ConfigMap và Secret lưu trữ các cấu hình hoặc dữ liệu nhạy cảm được sử dụng bởi các đối tượng Kubernetes khác, chẳng hạn như Pod. Nguồn dữ liệu gốc (source of truth) của ConfigMap hoặc Secret thường nằm bên ngoài cụm (cluster), ví dụ như tệp .properties hoặc tệp khóa SSH. Kustomize cung cấp các tính năng `secretGenerator` và `configMapGenerator` để tạo Secret và ConfigMap từ các tệp tin hoặc các giá trị trực tiếp (literals). 

Các [`Service`](https://kubernetes.io/docs/concepts/services-networking/service/) trong Kubernetes
Service API, một thành phần của Kubernetes, là một lớp trừu tượng giúp bạn công khai (expose) các nhóm Pod thông qua mạng. Mỗi đối tượng Service định nghĩa một tập hợp logic các điểm cuối (endpoint) — thường là các Pod — cùng với chính sách quy định cách thức truy cập vào các Pod đó.

Ví dụ, hãy xem xét một hệ thống backend xử lý hình ảnh không lưu trạng thái (stateless) đang chạy với 3 bản sao (replica). Các bản sao này có thể thay thế cho nhau; các thành phần frontend không cần quan tâm cụ thể mình đang kết nối với backend nào. Ngay cả khi các Pod thực tế tạo nên tập hợp backend đó thay đổi, các client ở phía frontend cũng không cần phải biết về sự thay đổi này, cũng như không cần tự mình theo dõi danh sách các backend hiện có.


- Nếu lỗi với kind cần tạo lại đây là các lệnh để áp dụng lại cấu hình trước đó
```
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/overlays/local/postgres.yaml
kubectl apply -f k8s/base/configmap.yaml
kubectl apply -f k8s/overlays/local/secret.yaml
```
## user-service (Các service khác làm tương tự)

- Build image user-service để đảm bảo đã có container này trước

```
docker build -t ecommerce/user-service:local services/user-service
```

- verify
```
docker images | grep ecommerce/user-service
```

- Load image vào Kind
```
kind load docker-image ecommerce/user-service:local --name ecommerce-local
```
- verify
```
docker exec ecommerce-local-control-plane crictl images | grep ecommerce/user-service
```
- Apply User Service + Verify
```
kubectl apply -k k8s/base/user-service
kubectl get pods -n ecommerce
```
- kiểm tra /health và /ready
```
kubectl port-forward -n ecommerce svc/user-service 8001:8001
```

Sau khi tạo các service xong không cần phải apply từng service nữa chỉ cần dùng thư mục chứa các configuaration để mà apply nhé~
```
kubectl apply -k k8s/overlays/local
```

## Cài NGINX Ingress Controller cho Kind
Dùng manifest chính thức dành cho Kind
```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
```

Verify
```
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
```

Kiểm tra IngressClass
```
kubectl get ingressclass
```
NAME  |  CONTROLLER|
| --- | --- |
nginx|   k8s.io/ingress-nginx|

## Tạm dừng container mà không xóa dữ liệu

```
docker stop ecommerce-local-control-plane ecommerce-local-worker ecommerce-local-worker2
#Khi nào muốn bật lại:
docker start ecommerce-local-control-plane ecommerce-local-worker ecommerce-local-worker2
```

