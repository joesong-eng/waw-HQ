<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    /**
     * Run the migrations.
     * M3: Device Management - 設備資產表
     */
    public function up(): void
    {
        Schema::create('devices', function (Blueprint $table) {
            $table->id();

            // 物理識別
            $table->string('chip_id', 50)->unique()->comment('物理 MAC/SN，如 ESP32-A1B2C3');

            // 歸屬關係
            $table->unsignedBigInteger('owner_id')->index()->comment('設備商 MO，FK -> users.id');
            $table->unsignedBigInteger('venue_id')->nullable()->index()->comment('掛載場地，FK -> venues.id');

            // 基本資訊
            $table->string('name', 100)->nullable()->comment('設備別名');
            $table->enum('type', ['claw', 'arcade', 'washer', 'gambling', 'other'])->nullable()->comment('機台類型');
            $table->unsignedInteger('pulse_ratio')->default(10)->comment('1脈衝=多少金額');

            // 經營模式與分潤
            $table->enum('placement_type', ['self_operated', 'consignment'])->default('self_operated')->comment('自營/寄台');
            $table->decimal('share_device_owner', 5, 2)->default(100.00)->comment('設備商分成 %');
            $table->decimal('share_venue_owner', 5, 2)->default(0.00)->comment('場地商分成 %');
            $table->decimal('promo_budget_monthly', 10, 2)->default(0.00)->comment('每月公關額度');
            $table->decimal('promo_budget_used', 10, 2)->default(0.00)->comment('本月已使用額度');

            // 狀態
            $table->enum('status', ['pending_setup', 'active', 'maintenance', 'lost', 'stolen'])->default('pending_setup')->index()->comment('設備狀態');

            // 累計數據 (Basic Tier Feature)
            $table->unsignedBigInteger('lifetime_credit_in')->default(0)->comment('累計開分/投幣金額');
            $table->unsignedBigInteger('lifetime_credit_out')->default(0)->comment('累計洗分/兌幣金額');

            // 即時狀態
            $table->timestamp('last_seen_at')->nullable()->comment('最後心跳時間');
            $table->boolean('is_online')->default(false)->index()->comment('當前是否在線');

            // 設備配置
            $table->json('config_json')->nullable()->comment('設備物理參數 (爪力、防抖等)');
            $table->string('firmware_ver', 20)->nullable()->comment('韌體版本');

            $table->timestamps();

            // 索引
            $table->index(['owner_id', 'status']);
            $table->index(['venue_id', 'status']);
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('devices');
    }
};
