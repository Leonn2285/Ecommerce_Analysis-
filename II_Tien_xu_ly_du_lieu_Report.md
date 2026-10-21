# II. TIỀN XỬ LÝ DỮ LIỆU

## 2.1 EDA

### Mục tiêu và phạm vi

EDA được thực hiện trên toàn bộ file `data/marketplace_products_combined_11k.csv`, gồm 11.050 quan sát và 16 biến. Các biểu đồ sử dụng toàn bộ dữ liệu đã gộp, không lọc theo `record_origin`. File này gồm 10.000 quan sát tổng hợp và 1.050 quan sát crawl; do đó, các thống kê dưới đây mô tả tập dữ liệu phục vụ bài tập, không phải ước lượng đại diện cho toàn bộ thị trường hay toàn bộ sản phẩm đang bán trên các sàn.

Tập dữ liệu có ba sàn: Shopee 3.771 quan sát (34,1%), Tiki 3.705 (33,5%) và Lazada 3.574 (32,3%). Chênh lệch số lượng giữa các sàn nhỏ, nên việc so sánh mô tả theo sàn không bị chi phối nhiều bởi riêng tổng kích thước mẫu. Dù vậy, dữ liệu giữa các sàn có thể khác nhau về cách hiển thị giá, đánh giá và lượt bán.

### Quy mô theo sàn và danh mục

**Vị trí chèn Hình 2.1:** đặt ngay sau đoạn giới thiệu quy mô theo sàn và danh mục này.

> **[CHÈN HÌNH 2.1 TẠI ĐÂY]** Heatmap số lượng sản phẩm theo sàn thương mại điện tử và danh mục.
>
> *Nguồn: Tác giả trực quan hóa từ toàn bộ dữ liệu `marketplace_products_combined_11k.csv`.*

Heatmap cho thấy mức độ phủ dữ liệu tương đối rộng ở cả chín danh mục. Tổng số quan sát theo danh mục dao động từ 1.025 ở **Thời trang trẻ em** đến 1.381 ở **Sức khỏe**. Một số chênh lệch đáng chú ý giữa các ô là Sức khỏe trên Shopee có 715 quan sát, trong khi Sức khỏe trên Tiki có 285; Điện tử trên Tiki có 487, cao hơn Shopee (413) và Lazada (404). Khi so sánh một danh mục cụ thể giữa các sàn, cần đọc số lượng mẫu đi kèm và tránh xem chênh lệch thô là khác biệt chắc chắn về thị trường.

### Phân phối giá

Trong 11.050 dòng, biến `price` có 10.747 giá trị, tức thiếu 303 giá trị (2,7%). Giá trung vị là **165.000 VND**, thấp hơn đáng kể so với trung bình **430.821 VND**. 75% giá không vượt quá 410.000 VND, trong khi phân vị 95 là 1.670.000 VND và giá lớn nhất là 12.965.000 VND. Khoảng cách giữa trung bình và trung vị cùng phần đuôi phải dài cho thấy phân phối giá lệch phải: phần lớn sản phẩm ở mức giá thấp hoặc trung bình, còn một nhóm nhỏ sản phẩm giá cao kéo trung bình lên.

**Vị trí chèn Hình 2.2:** đặt ngay sau đoạn mô tả thống kê giá ở trên, trước phần nhận xét biểu đồ.

> **[CHÈN HÌNH 2.2 TẠI ĐÂY]** Boxplot phân phối giá theo sàn và danh mục; trục tung ở thang logarit, các điểm ngoại lệ được ẩn để dễ quan sát trung vị và khoảng tứ phân vị.
>
> *Nguồn: Tác giả trực quan hóa từ toàn bộ dữ liệu `marketplace_products_combined_11k.csv`.*

Biểu đồ boxplot được vẽ theo từng sàn và danh mục, dùng trục logarit để thể hiện được đồng thời các mức giá chênh lệch lớn; các điểm ngoại lệ được ẩn khỏi boxplot để hộp và trung vị dễ đọc hơn. Biểu đồ cho phép nhận diện mức giá điển hình và độ phân tán giữa các nhóm, nhưng không loại bỏ hay thay đổi giá gốc. Nên sử dụng trung vị, các phân vị hoặc log giá khi phân tích tiếp theo thay vì chỉ dựa vào trung bình. Giá gốc `original_price` chỉ có 3.367 giá trị (30,5%), nên mọi so sánh có sử dụng giá gốc hoặc mức giảm giá cần nêu rõ số quan sát khả dụng.

### Biến số khác và mức độ phân tán

`discount_percent` có 8.148 giá trị; trung vị là 35%, phân vị 75 là 48%, và giá trị cao nhất là 100%. `rating` chỉ có 3.110 quan sát; trung vị 4,9 trên thang 5 điểm. Các rating được giữ trong khoảng 1–5 sau bước kiểm tra hợp lệ. `review_count` có 3.310 giá trị, trung vị 49 và lớn nhất 48.201. `sold_count_estimate` có 8.742 giá trị; trung vị 125, phân vị 75 là 997, trong khi lớn nhất là 970.500. Hai biến về lượt đánh giá và lượt bán có phân phối lệch phải mạnh, nên cân nhắc dùng `log1p` hoặc thống kê phân vị cho mô hình và biểu đồ.

### Bản ghi trùng lặp

Không phát hiện dòng trùng hoàn toàn; cũng không có trùng theo khóa kết hợp `(platform, product_id)`. Vì vậy, không loại bỏ bản ghi nào theo tiêu chí trùng lặp này. Kết quả này chỉ xác nhận tính duy nhất trong phạm vi khóa hiện có; cùng một mặt hàng có thể vẫn xuất hiện dưới mã sản phẩm khác nhau.

## 2.2 Chuẩn hóa dữ liệu

Quá trình chuẩn hóa được thực hiện trên bản sao `df_clean` để giữ nguyên DataFrame EDA ban đầu. Nhãn danh mục được loại bỏ khoảng trắng thừa và nhãn `health` được chuẩn hóa về **Sức khỏe**. Các cột `price`, `original_price`, `discount_percent`, `rating` và `review_count` được chuyển sang kiểu số; giá trị không chuyển đổi được sẽ thành null để không bị hiểu nhầm là một con số hợp lệ.

Các giá trị `price` bằng 0 được xem là không hợp lệ trong ngữ cảnh giá bán sản phẩm và chuyển thành null. Rating nằm ngoài khoảng 0–5 được xem là lỗi parse và chuyển thành null. Trong file tổng hiện tại không còn giá bằng 0 hoặc rating ngoài khoảng này. Những biến giá, rating, đánh giá và lượt bán còn thiếu được giữ nguyên null vì nguồn không cung cấp thông tin; không dùng trung bình hoặc median để tự tạo thông tin. Trường `currency` trống được điền `VND`, phù hợp với phạm vi các sàn Việt Nam của dự án.

Giá trị lượt bán gốc `sold_count` được giữ lại. Từ hậu tố `k`/`K`, `m`/`M` và dấu `+`, quy trình tạo `sold_count_estimate` dạng số để hỗ trợ phân tích; đồng thời `sold_count_is_lower_bound` ghi nhận các giá trị có dấu `+` là cận dưới. Các con số này là giá trị xấp xỉ từ cách nền tảng hiển thị, không nên diễn giải như số đơn hàng chính xác.

## 2.3 Kiểm tra dữ liệu bị thiếu

Biểu đồ tỷ lệ null cho thấy dữ liệu thiếu tập trung ở một số trường vốn phụ thuộc vào việc sàn hoặc trang sản phẩm có hiển thị thông tin hay không. Bảng dưới đây tổng hợp số lượng và tỷ lệ null trên toàn bộ 11.050 dòng:

**Vị trí chèn Hình 2.3:** đặt sau câu giới thiệu biểu đồ tỷ lệ null và ngay trước bảng số liệu dưới đây.

> **[CHÈN HÌNH 2.3 TẠI ĐÂY]** Tỷ lệ dữ liệu thiếu theo biến trên toàn bộ tập dữ liệu.
>
> *Nguồn: Tác giả trực quan hóa từ toàn bộ dữ liệu `marketplace_products_combined_11k.csv`.*

| Biến | Số giá trị thiếu | Tỷ lệ |
|---|---:|---:|
| `rating` | 7.940 | 71,9% |
| `review_count` | 7.740 | 70,0% |
| `original_price` | 7.683 | 69,5% |
| `seller_location` | 5.095 | 46,1% |
| `discount_percent` | 2.902 | 26,3% |
| `sold_count`, `sold_count_estimate`, `sold_count_is_lower_bound` | 2.308 mỗi biến | 20,9% |
| `price`, `price_outlier` | 303 mỗi biến | 2,7% |
| Các biến còn lại | 0 | 0,0% |

Không điền giá trị giả cho `rating`, `review_count`, `original_price`, `seller_location`, `discount_percent` và lượt bán vì null ở đây thường có nghĩa là không được cung cấp hoặc không lấy được từ nguồn. Khi phân tích từng biến, cần nêu số dòng có dữ liệu thực tế; khi huấn luyện mô hình, có thể loại các biến thiếu quá nhiều khỏi một mô hình cụ thể, thêm cờ thiếu, hoặc dùng pipeline xử lý null được fit trên tập huấn luyện. Không nên điền median hàng loạt vì sẽ làm giảm độ biến thiên và có thể tạo quan hệ không tồn tại trong dữ liệu.

## 2.4 Kiểm tra biến outliers

Giá có phân phối lệch phải và phạm vi rộng, nên dùng quy tắc IQR riêng theo từng cặp **sàn × danh mục**. Với mỗi nhóm, các giá nhỏ hơn `Q1 − 1,5 × IQR` hoặc lớn hơn `Q3 + 1,5 × IQR` được gắn cờ. Cách tính theo nhóm giúp so sánh giá trong bối cảnh sản phẩm và sàn tương đồng hơn; biểu đồ heatmap thể hiện tỷ lệ bị gắn cờ trên số giá quan sát của từng nhóm.

**Vị trí chèn Hình 2.4:** đặt ngay sau đoạn giải thích cách dùng quy tắc IQR, trước khi diễn giải các nhóm có tỷ lệ cao.

> **[CHÈN HÌNH 2.4 TẠI ĐÂY]** Heatmap tỷ lệ giá bị gắn cờ ngoại lệ theo sàn và danh mục, sử dụng ngưỡng IQR riêng cho từng nhóm.
>
> *Nguồn: Tác giả tính toán và trực quan hóa từ toàn bộ dữ liệu `marketplace_products_combined_11k.csv`.*

Tổng cộng có **637/10.747 giá** được gắn cờ (xấp xỉ 5,9%). Tỷ lệ cao nhất trong heatmap là **Điện tử trên Tiki (15,4%)**; tiếp theo là **Văn phòng phẩm trên Shopee (11,9%)**, **Điện tử trên Lazada (9,7%)** và **Thực phẩm & đồ uống trên Lazada (8,6%)**. Một số nhóm không có giá bị gắn cờ theo ngưỡng IQR, ví dụ Sức khỏe trên Tiki và Văn phòng phẩm trên Tiki. Đây là kết quả của ngưỡng trong từng nhóm, không đồng nghĩa giá của các nhóm đó giống nhau.

Các giá bị gắn cờ được giữ nguyên và chỉ đánh dấu trong `price_outlier`; không xóa và không winsorize. Một sản phẩm có giá cao có thể là sản phẩm hợp lệ, đặc biệt trong nhóm điện tử hoặc điện gia dụng. Khi xây dựng mô hình, nên so sánh kết quả có và không có các điểm bị gắn cờ, đồng thời cân nhắc log-transform giá. Tỷ lệ ngoại lệ phụ thuộc vào quy tắc IQR và quy mô từng nhóm, nên đây là tín hiệu để xem xét chứ không phải kết luận rằng bản ghi sai.

### Ghi chú về cách diễn giải

Toàn bộ số liệu và biểu đồ trong phần này được tính trên file tổng đã gộp như yêu cầu. Vì 10.000/11.050 dòng (90,5%) là dữ liệu tổng hợp, các phát hiện về giá, đánh giá, lượt bán và sự khác biệt giữa các sàn chủ yếu phản ánh cách tạo dữ liệu tổng hợp trong tập hiện tại. Khi viết kết luận thực nghiệm về hành vi thị trường, cần trình bày rõ giới hạn này và tránh khái quát hóa các tỷ lệ quan sát được thành đặc điểm thực tế của Shopee, Tiki hoặc Lazada.
